"""Pagine web per login, layout protetto e logout."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.api.dependencies import (
    DatabaseSession,
    SessionCookie,
    get_current_user,
)
from app.db.models import User
from app.domain.auth_contracts import LoginRequest
from app.domain.vocabulary import Role
from app.security.authentication import (
    authenticate_user,
    revoke_user_session,
    start_user_session,
)
from app.security.session_cookie import delete_session_cookie, set_session_cookie


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


def _login_context(email: str = "", error: str | None = None) -> dict[str, object]:
    return {
        "page_title": "Accedi",
        "body_class": "login-page",
        "email": email,
        "error": error,
    }


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
def app_home(request: Request, current_user: WebUser) -> HTMLResponse:
    """Mostra la base protetta che verrà estesa dalle prossime attività."""

    return templates.TemplateResponse(
        request=request,
        name="app_home.html",
        context={
            "page_title": "Area di lavoro",
            "body_class": "workspace-page",
            "current_user": current_user,
            "role_label": ROLE_LABELS[current_user.role],
        },
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
