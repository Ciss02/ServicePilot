"""Pagine web per login, layout protetto e logout."""

from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Path as PathParameter,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    DatabaseSession,
    SessionCookie,
    get_current_user,
)
from app.db.models import Site, Ticket, User
from app.domain.auth_contracts import LoginRequest
from app.domain.vocabulary import Role
from app.security.authentication import (
    authenticate_user,
    revoke_user_session,
    start_user_session,
)
from app.security.session_cookie import delete_session_cookie, set_session_cookie
from app.tickets.queries import get_visible_ticket, list_visible_tickets
from app.web.ticket_presenters import (
    EmployeeTicketView,
    present_employee_ticket,
    summarize_employee_tickets,
)


TEMPLATES_DIRECTORY = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIRECTORY)
router = APIRouter(include_in_schema=False)

ROLE_LABELS = {
    Role.EMPLOYEE: "Dipendente",
    Role.TECHNICIAN: "Tecnico IT",
    Role.ADMIN: "Amministratore",
}
LOGIN_ERROR = "Controlla email e password e riprova."


def get_web_user(
    session: DatabaseSession,
    session_token: SessionCookie = None,
) -> User:
    """Richiede una sessione valida e, se manca, rimanda alla pagina di accesso."""

    try:
        return get_current_user(session=session, session_token=session_token)
    except HTTPException as error:
        if error.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/login"},
            ) from error
        raise


WebUser = Annotated[User, Depends(get_web_user)]
WebTicketId = Annotated[int, PathParameter(gt=0)]


def _login_context(email: str = "", error: str | None = None) -> dict[str, object]:
    return {
        "page_title": "Accedi",
        "body_class": "login-page",
        "email": email,
        "error": error,
    }


def _workspace_context(current_user: User, page_title: str) -> dict[str, object]:
    """Prepara identità e titolo condivisi dalle pagine autenticate."""

    return {
        "page_title": page_title,
        "body_class": "workspace-page",
        "current_user": current_user,
        "role_label": ROLE_LABELS[current_user.role],
    }


def _present_tickets(
    session: Session,
    tickets: list[Ticket],
) -> list[EmployeeTicketView]:
    """Carica in gruppo i nomi collegati e prepara i ticket per i template."""

    site_ids = {ticket.site_id for ticket in tickets}
    technician_ids = {
        ticket.assigned_technician_id
        for ticket in tickets
        if ticket.assigned_technician_id is not None
    }
    sites = (
        list(session.scalars(select(Site).where(Site.id.in_(site_ids))).all())
        if site_ids
        else []
    )
    technicians = (
        list(session.scalars(select(User).where(User.id.in_(technician_ids))).all())
        if technician_ids
        else []
    )
    sites_by_id = {site.id: site.name for site in sites}
    technicians_by_id = {user.id: user.display_name for user in technicians}

    return [
        present_employee_ticket(
            ticket,
            site_name=sites_by_id.get(ticket.site_id, "Sede non disponibile"),
            technician_name=(
                technicians_by_id.get(
                    ticket.assigned_technician_id,
                    "Tecnico non disponibile",
                )
                if ticket.assigned_technician_id is not None
                else "Non ancora assegnato"
            ),
        )
        for ticket in tickets
    ]


@router.get("/", response_class=HTMLResponse)
def index() -> RedirectResponse:
    """Porta il visitatore al punto di ingresso dell'applicazione."""

    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    session: DatabaseSession,
    session_token: SessionCookie = None,
) -> Response:
    """Mostra il form oppure rimanda all'area già autenticata."""

    if session_token:
        try:
            get_current_user(session=session, session_token=session_token)
        except HTTPException:
            pass
        else:
            return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=_login_context(),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/login", response_class=HTMLResponse)
def submit_login(
    request: Request,
    session: DatabaseSession,
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
) -> Response:
    """Controlla il form e apre una sessione usando le stesse regole delle API."""

    try:
        credentials = LoginRequest.model_validate(
            {"email": email, "password": password}
        )
    except ValidationError:
        credentials = None

    user = authenticate_user(session, credentials) if credentials else None
    if user is None:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=_login_context(email=email.strip()[:254], error=LOGIN_ERROR),
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Cache-Control": "no-store"},
        )

    token = start_user_session(session, user)
    response = RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    set_session_cookie(response, token)
    return response


@router.get("/app", response_class=HTMLResponse)
def app_home(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
) -> HTMLResponse:
    """Mostra l'area personale del dipendente o la base degli altri ruoli."""

    if current_user.role is Role.EMPLOYEE:
        tickets = list_visible_tickets(session, current_user)
        context = _workspace_context(current_user, "I miei ticket")
        context.update(
            {
                "tickets": _present_tickets(session, tickets),
                "summary": summarize_employee_tickets(tickets),
            }
        )
        return templates.TemplateResponse(
            request=request,
            name="employee_dashboard.html",
            context=context,
            headers={"Cache-Control": "no-store"},
        )

    return templates.TemplateResponse(
        request=request,
        name="app_home.html",
        context=_workspace_context(current_user, "Area di lavoro"),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/app/tickets/{ticket_id}", response_class=HTMLResponse)
def employee_ticket_detail(
    request: Request,
    ticket_id: WebTicketId,
    session: DatabaseSession,
    current_user: WebUser,
) -> Response:
    """Mostra al dipendente soltanto il dettaglio di una propria richiesta."""

    if current_user.role is not Role.EMPLOYEE:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

    ticket = get_visible_ticket(session, current_user, ticket_id)
    if ticket is None:
        return templates.TemplateResponse(
            request=request,
            name="employee_ticket_not_found.html",
            context=_workspace_context(current_user, "Ticket non trovato"),
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"Cache-Control": "no-store"},
        )

    context = _workspace_context(current_user, f"Ticket SP-{ticket.id:04d}")
    context["ticket"] = _present_tickets(session, [ticket])[0]
    return templates.TemplateResponse(
        request=request,
        name="employee_ticket_detail.html",
        context=context,
        headers={"Cache-Control": "no-store"},
    )


@router.post("/logout")
def web_logout(
    session: DatabaseSession,
    session_token: SessionCookie = None,
) -> RedirectResponse:
    """Chiude la sessione web e torna alla pagina di accesso."""

    revoke_user_session(session, session_token)
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    delete_session_cookie(response)
    return response
