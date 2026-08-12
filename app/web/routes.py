"""Pagine web per login, layout protetto e logout."""

import secrets
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path as PathParameter,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import (
    list_audit_events,
    list_ticket_audit_events,
    present_audit_events,
)
from app.ai import (
    AIModelError,
    AvailableSite,
    TicketClassificationPersistenceError,
    TicketIntakeField,
    classify_confirmed_ticket,
    extract_ticket_details,
)
from app.ai.dependencies import AIModelDependency, EmbeddingModelDependency
from app.actions import (
    ActionAlreadyDecidedError,
    ActionDecisionPersistenceError,
    ActionNotFoundError,
    ActionProposalDataError,
    decide_action_proposal,
)
from app.actions.dependencies import ActionServiceClientDependency
from app.api.dependencies import (
    DatabaseSession,
    SessionCookie,
    get_current_user,
)
from app.db.models import AuditEvent, KnowledgeDocument, KnowledgeSegment, Site, Ticket, User
from app.domain.auth_contracts import LoginRequest
from app.domain.ticket_contracts import TicketClassification, TicketCreate, TicketUpdate
from app.domain.ticket_intake import (
    TicketCreationKeyInput,
    TicketMissingDetailsInput,
    TicketProblemInput,
)
from app.domain.ticket_workflow import ALLOWED_STATUS_TRANSITIONS
from app.domain.vocabulary import ActionDecision, AuditActorType, Role
from app.knowledge import (
    EXTRACTION_FAILED,
    EXTRACTION_PENDING,
    EXTRACTION_READY,
    INDEX_FAILED,
    INDEX_PENDING,
    INDEX_READY,
    KnowledgeDocumentPersistenceError,
    KnowledgeDocumentProcessingError,
    KnowledgeDocumentValidationError,
    KnowledgeIndexingError,
    KnowledgeSearchError,
    KnowledgeSearchValidationError,
    TicketSolutionPersistenceError,
    get_knowledge_storage_directory,
    index_knowledge_document,
    generate_ticket_solution,
    list_ticket_solution_sources,
    process_knowledge_document,
    search_knowledge,
    store_knowledge_document,
)
from app.security.authentication import (
    authenticate_user,
    revoke_user_session,
    start_user_session,
)
from app.security.session_cookie import delete_session_cookie, set_session_cookie
from app.tickets.creation import (
    TicketPersistenceError,
    TicketSiteNotFoundError,
    create_confirmed_ticket,
)
from app.tickets.management import (
    ClassificationReviewRequiredError,
    InvalidStatusTransitionError,
    ManagedTechnicianNotFoundError,
    ManagedTechnicianUnavailableError,
    ManagedTicketNotFoundError,
    ResolutionRequiredError,
    TicketUpdatePersistenceError,
    update_managed_ticket,
)
from app.tickets.queries import get_visible_ticket, list_visible_tickets
from app.web.technician_presenters import (
    CATEGORY_OPTIONS,
    IMPACT_OPTIONS,
    STATUS_OPTIONS,
    URGENCY_OPTIONS,
    TechnicianAssignmentFilter,
    TechnicianPriorityFilter,
    TechnicianSort,
    TechnicianStatusFilter,
    filter_and_sort_technician_tickets,
    list_active_technical_users,
    present_technician_tickets,
    summarize_technician_queue,
)
from app.web.action_presenters import present_action_proposals
from app.web.ticket_presenters import (
    EmployeeTicketFilter,
    EmployeeTicketView,
    filter_employee_tickets,
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
INTAKE_ERRORS = {
    "description": "Descrivi il problema usando almeno 10 caratteri.",
    "title": "Inserisci un titolo breve di almeno 5 caratteri.",
    "site_id": "Seleziona una sede disponibile.",
    "service": "Indica il servizio o lo strumento coinvolto.",
    "affected_users": "Inserisci un numero di persone compreso tra 1 e 10.000.",
}
ALL_INTAKE_FIELDS = [field.value for field in TicketIntakeField]
INTAKE_FIELD_LABELS = {
    TicketIntakeField.TITLE.value: "un titolo breve",
    TicketIntakeField.SITE_ID.value: "la sede interessata",
    TicketIntakeField.SERVICE.value: "il servizio o lo strumento coinvolto",
    TicketIntakeField.AFFECTED_USERS.value: "quante persone sono coinvolte",
}


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
EmployeeTicketFilterParameter = Annotated[
    EmployeeTicketFilter,
    Query(alias="filter"),
]
TechnicianStatusFilterParameter = Annotated[
    TechnicianStatusFilter,
    Query(alias="status"),
]
TechnicianAssignmentFilterParameter = Annotated[
    TechnicianAssignmentFilter,
    Query(alias="assignment"),
]
TechnicianPriorityFilterParameter = Annotated[
    TechnicianPriorityFilter,
    Query(alias="priority"),
]
TechnicianSortParameter = Annotated[TechnicianSort, Query(alias="sort")]


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


def _intake_context(
    current_user: User,
    *,
    step: str,
    sites: list[Site] | None = None,
    values: dict[str, object] | None = None,
    errors: dict[str, str] | None = None,
    requested_fields: list[str] | None = None,
    ai_assisted: bool = False,
) -> dict[str, object]:
    """Prepara uno dei tre passaggi della conversazione guidata."""

    context = _workspace_context(current_user, "Nuova richiesta")
    context.update(
        {
            "step": step,
            "sites": sites or [],
            "values": values or {},
            "errors": errors or {},
            "requested_fields": (
                requested_fields
                if requested_fields is not None
                else ALL_INTAKE_FIELDS
            ),
            "ai_assisted": ai_assisted,
            "missing_details": [
                INTAKE_FIELD_LABELS[field]
                for field in (requested_fields or [])
                if field in INTAKE_FIELD_LABELS
            ],
        }
    )
    return context


def _validation_errors(error: ValidationError) -> dict[str, str]:
    """Converte gli errori tecnici in indicazioni semplici per il modulo."""

    return {
        str(item["loc"][0]): INTAKE_ERRORS[str(item["loc"][0])]
        for item in error.errors()
        if item["loc"] and str(item["loc"][0]) in INTAKE_ERRORS
    }


def _active_sites(session: Session) -> list[Site]:
    """Mostra soltanto sedi attive, ordinate per nome."""

    return list(
        session.scalars(
            select(Site).where(Site.is_active.is_(True)).order_by(Site.name)
        ).all()
    )


def _employee_only(current_user: User) -> RedirectResponse | None:
    """Rimanda gli altri ruoli alla loro area senza mostrare il modulo dipendente."""

    if current_user.role is not Role.EMPLOYEE:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _admin_only(current_user: User) -> RedirectResponse | None:
    """Nasconde gli strumenti della knowledge base a chi non è amministratore."""

    if current_user.role is not Role.ADMIN:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    return None


def _knowledge_context(
    session: Session,
    current_user: User,
    *,
    uploaded: bool = False,
    extraction: str | None = None,
    indexing: str | None = None,
    query: str = "",
    search_results: list[dict[str, object]] | None = None,
    search_error: str | None = None,
    error: str | None = None,
) -> dict[str, object]:
    """Prepara l'elenco dei documenti senza rivelarne il percorso interno."""

    documents = list(
        session.scalars(
            select(KnowledgeDocument).order_by(
                KnowledgeDocument.created_at.desc(),
                KnowledgeDocument.id.desc(),
            )
        ).all()
    )
    uploader_ids = {document.uploaded_by_user_id for document in documents}
    uploaders = (
        list(session.scalars(select(User).where(User.id.in_(uploader_ids))).all())
        if uploader_ids
        else []
    )
    uploader_names = {uploader.id: uploader.display_name for uploader in uploaders}
    segment_counts = dict(
        session.execute(
            select(KnowledgeSegment.document_id, func.count(KnowledgeSegment.id))
            .group_by(KnowledgeSegment.document_id)
        ).all()
    )

    def extraction_presentation(document: KnowledgeDocument) -> tuple[str, str]:
        segment_count = segment_counts.get(document.id, 0)
        if document.extraction_status == EXTRACTION_READY:
            segment_label = (
                f"{segment_count} segmento"
                if segment_count == 1
                else f"{segment_count} segmenti"
            )
            if document.index_status == INDEX_READY:
                return f"{segment_label} · Indicizzato", "ready"
            if document.index_status == INDEX_FAILED:
                return f"{segment_label} · Indice non disponibile", "failed"
            return f"{segment_label} · Da indicizzare", "pending"
        if document.extraction_status == EXTRACTION_FAILED:
            return "Testo non estratto", "failed"
        return "Da elaborare", "pending"

    presented_documents = []
    for document in documents:
        state, state_class = extraction_presentation(document)
        presented_documents.append(
            {
                "id": document.id,
                "filename": document.original_filename,
                "format": (
                    "PDF"
                    if document.content_type == "application/pdf"
                    else "Markdown"
                ),
                "size": f"{document.size_bytes / 1024:.1f} KB",
                "uploaded_by": uploader_names.get(
                    document.uploaded_by_user_id, "Amministratore demo"
                ),
                "created_at": document.created_at.strftime("%d/%m/%Y · %H:%M"),
                "state": state,
                "state_class": state_class,
            }
        )
    context = _workspace_context(current_user, "Knowledge base")
    context.update(
        {
            "documents": presented_documents,
            "uploaded": uploaded,
            "extraction": extraction,
            "indexing": indexing,
            "query": query,
            "search_results": search_results or [],
            "search_error": search_error,
            "upload_error": error,
        }
    )
    return context


def _audit_context(
    session: Session,
    current_user: User,
    *,
    actor_type: AuditActorType | None = None,
    ticket_id: int | None = None,
) -> dict[str, object]:
    """Prepara la vista amministrativa senza esporre il JSON interno."""

    events = list_audit_events(
        session,
        actor_type=actor_type,
        ticket_id=ticket_id,
    )
    count_rows = session.execute(
        select(AuditEvent.actor_type, func.count(AuditEvent.id)).group_by(
            AuditEvent.actor_type
        )
    ).all()
    counts = {actor.value: count for actor, count in count_rows}
    context = _workspace_context(current_user, "Audit log")
    context.update(
        {
            "audit_events": present_audit_events(session, events),
            "selected_actor": actor_type.value if actor_type else "all",
            "ticket_filter": str(ticket_id or ""),
            "total_events": sum(counts.values()),
            "human_events": counts.get(AuditActorType.HUMAN.value, 0),
            "ai_events": counts.get(AuditActorType.AI.value, 0),
            "system_events": counts.get(AuditActorType.SYSTEM.value, 0),
        }
    )
    return context


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


def _technical_ticket_context(
    session: Session,
    current_user: User,
    ticket: Ticket,
    *,
    values: dict[str, str] | None = None,
    errors: dict[str, str] | None = None,
    updated: bool = False,
    classification_reviewed: bool = False,
    solution_attempted: bool = False,
    solution_error: str | None = None,
    action_result: str | None = None,
    action_error: str | None = None,
) -> dict[str, object]:
    """Prepara dettaglio, scelte consentite e valori del modulo tecnico."""

    ticket_view = present_technician_tickets(session, [ticket])[0]
    allowed_statuses = {ticket.status, *ALLOWED_STATUS_TRANSITIONS[ticket.status]}
    default_values = {
        "status": ticket_view.status_code,
        "assigned_technician_id": str(ticket_view.assigned_technician_id or ""),
        "assigned_group": ticket_view.assigned_group,
        "category": ticket_view.category_code,
        "subcategory": ticket_view.subcategory,
        "impact": ticket_view.impact_code,
        "urgency": ticket_view.urgency_code,
        "technician_note": ticket_view.technician_note,
        "resolution": ticket_view.resolution,
    }
    context = _workspace_context(current_user, f"Gestisci {ticket_view.code}")
    try:
        action_proposals = present_action_proposals(session, ticket.id)
        action_load_error = None
    except ActionProposalDataError:
        action_proposals = []
        action_load_error = (
            "Le azioni salvate non possono essere mostrate in modo affidabile."
        )

    context.update(
        {
            "ticket": ticket_view,
            "technicians": list_active_technical_users(session),
            "status_options": [
                option
                for option in STATUS_OPTIONS
                if option[0] in {item.value for item in allowed_statuses}
            ],
            "category_options": CATEGORY_OPTIONS,
            "impact_options": IMPACT_OPTIONS,
            "urgency_options": URGENCY_OPTIONS,
            "values": values or default_values,
            "errors": errors or {},
            "updated": updated,
            "classification_reviewed": classification_reviewed,
            "solution_attempted": solution_attempted,
            "solution_error": solution_error,
            "solution_sources": list_ticket_solution_sources(session, ticket.id),
            "action_proposals": action_proposals,
            "action_result": action_result,
            "action_error": action_error or action_load_error,
            "audit_events": present_audit_events(
                session,
                list_ticket_audit_events(session, ticket.id),
            ),
        }
    )
    return context


def _technical_update_payload(
    *,
    status_value: str,
    assigned_technician_id: str,
    assigned_group: str,
    category: str,
    subcategory: str,
    impact: str,
    urgency: str,
    technician_note: str,
    resolution: str,
    review_classification: bool = False,
) -> tuple[TicketUpdate | None, dict[str, str], dict[str, str]]:
    """Converte il modulo in un contratto sicuro e messaggi comprensibili."""

    values = {
        "status": status_value,
        "assigned_technician_id": assigned_technician_id,
        "assigned_group": assigned_group[:100],
        "category": category,
        "subcategory": subcategory[:100],
        "impact": impact,
        "urgency": urgency,
        "technician_note": technician_note[:2_000],
        "resolution": resolution[:4_000],
    }
    errors: dict[str, str] = {}
    raw_payload: dict[str, object] = {"status": status_value}

    clean_technician_id = assigned_technician_id.strip()
    if clean_technician_id:
        if clean_technician_id.isdecimal() and int(clean_technician_id) > 0:
            raw_payload["assigned_technician_id"] = int(clean_technician_id)
        else:
            errors["assigned_technician_id"] = "Seleziona un tecnico disponibile."

    for field_name, value in {
        "assigned_group": assigned_group,
        "technician_note": technician_note,
        "resolution": resolution,
    }.items():
        if value.strip():
            raw_payload[field_name] = value

    classification_values = {
        "category": category,
        "subcategory": subcategory or None,
        "impact": impact,
        "urgency": urgency,
    }
    required_classification = (category, impact, urgency)
    if any(required_classification) and not all(required_classification):
        errors["classification"] = "Completa categoria, impatto e urgenza insieme."
    elif all(required_classification):
        try:
            raw_payload["classification"] = TicketClassification.model_validate(
                classification_values
            )
        except ValidationError:
            errors["classification"] = "Controlla i dati della classificazione."

    if review_classification:
        if not all(required_classification):
            errors["classification"] = (
                "Completa categoria, impatto e urgenza prima di confermare."
            )
        if not assigned_group.strip():
            errors["assigned_group"] = (
                "Indica il gruppo prima di confermare la classificazione."
            )
        if not errors:
            raw_payload["classification_reviewed"] = True

    if errors:
        return None, values, errors
    try:
        return TicketUpdate.model_validate(raw_payload), values, {}
    except ValidationError as error:
        for item in error.errors():
            field = str(item["loc"][0]) if item["loc"] else "update"
            if field == "status":
                errors[field] = "Seleziona uno stato consentito."
            elif field == "technician_note":
                errors[field] = "La nota deve contenere almeno 2 caratteri."
            elif field == "resolution":
                errors[field] = "La soluzione deve contenere almeno 10 caratteri."
            elif field == "assigned_group":
                errors[field] = "Il gruppo deve contenere almeno 2 caratteri."
            else:
                errors["update"] = "Controlla i dati inseriti e riprova."
        return None, values, errors


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
    selected_filter: EmployeeTicketFilterParameter = "all",
    technical_status: TechnicianStatusFilterParameter = "open",
    assignment: TechnicianAssignmentFilterParameter = "all",
    priority: TechnicianPriorityFilterParameter = "all",
    sort_by: TechnicianSortParameter = "priority",
) -> HTMLResponse:
    """Mostra l'area personale oppure la coda completa dei ruoli tecnici."""

    if current_user.role is Role.EMPLOYEE:
        tickets = list_visible_tickets(session, current_user)
        filtered_tickets = filter_employee_tickets(tickets, selected_filter)
        context = _workspace_context(current_user, "I miei ticket")
        context.update(
            {
                "tickets": _present_tickets(session, filtered_tickets),
                "summary": summarize_employee_tickets(tickets),
                "selected_filter": selected_filter,
                "total_tickets": len(tickets),
            }
        )
        return templates.TemplateResponse(
            request=request,
            name="employee_dashboard.html",
            context=context,
            headers={"Cache-Control": "no-store"},
        )

    tickets = list_visible_tickets(session, current_user)
    filtered_tickets = filter_and_sort_technician_tickets(
        tickets,
        current_user_id=current_user.id,
        status_filter=technical_status,
        assignment_filter=assignment,
        priority_filter=priority,
        sort_by=sort_by,
    )
    if assignment == "unassigned":
        active_summary = "unassigned"
    elif technical_status in {
        "waiting",
        "waiting_for_requester",
        "waiting_for_vendor",
    }:
        active_summary = "waiting"
    elif technical_status in {"completed", "resolved", "closed"}:
        active_summary = "completed"
    else:
        active_summary = "open"
    context = _workspace_context(current_user, "Coda tecnica")
    context.update(
        {
            "tickets": present_technician_tickets(session, filtered_tickets),
            "summary": summarize_technician_queue(tickets),
            "total_tickets": len(tickets),
            "technical_status": technical_status,
            "assignment": assignment,
            "priority": priority,
            "sort_by": sort_by,
            "active_summary": active_summary,
        }
    )
    return templates.TemplateResponse(
        request=request,
        name="technician_dashboard.html",
        context=context,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/app/new-ticket", response_class=HTMLResponse)
def new_ticket_start(
    request: Request,
    current_user: WebUser,
) -> Response:
    """Avvia la raccolta chiedendo una descrizione libera del problema."""

    if redirect := _employee_only(current_user):
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="employee_ticket_intake.html",
        context=_intake_context(current_user, step="problem"),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/app/knowledge", response_class=HTMLResponse)
def knowledge_documents(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
    embedding_model: EmbeddingModelDependency,
    uploaded: Annotated[bool, Query()] = False,
    extraction: Annotated[str | None, Query()] = None,
    indexing: Annotated[str | None, Query()] = None,
    q: Annotated[str, Query(max_length=500)] = "",
) -> Response:
    """Mostra all'amministratore l'upload e i documenti già conservati."""

    if redirect := _admin_only(current_user):
        return redirect

    search_results: list[dict[str, object]] = []
    search_error: str | None = None
    normalized_query = " ".join(q.split())
    if normalized_query:
        try:
            matches = search_knowledge(
                session,
                embedding_model,
                normalized_query,
            )
        except (KnowledgeSearchValidationError, KnowledgeSearchError) as error:
            search_error = str(error)
        else:
            search_results = [
                {
                    "filename": match.filename,
                    "source_section": match.source_section,
                    "content": match.content,
                    "score": f"{max(0, min(1, match.score)) * 100:.0f}%",
                }
                for match in matches
            ]
    return templates.TemplateResponse(
        request=request,
        name="admin_knowledge.html",
        context=_knowledge_context(
            session,
            current_user,
            uploaded=uploaded,
            extraction=extraction,
            indexing=indexing,
            query=normalized_query,
            search_results=search_results,
            search_error=search_error,
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/app/audit", response_class=HTMLResponse)
def audit_log(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
    actor: Annotated[AuditActorType | None, Query()] = None,
    ticket_id: Annotated[int | None, Query(gt=0)] = None,
) -> Response:
    """Mostra all'amministratore gli eventi più recenti e filtrabili."""

    if redirect := _admin_only(current_user):
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="admin_audit.html",
        context=_audit_context(
            session,
            current_user,
            actor_type=actor,
            ticket_id=ticket_id,
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/app/knowledge", response_class=HTMLResponse)
def upload_knowledge_document(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
    embedding_model: EmbeddingModelDependency,
    document: Annotated[UploadFile | None, File()] = None,
) -> Response:
    """Controlla e conserva un PDF o Markdown soltanto per l'amministratore."""

    if redirect := _admin_only(current_user):
        if document is not None:
            document.file.close()
        return redirect

    if document is None:
        error = "Seleziona un documento da caricare."
    else:
        try:
            stored_document = store_knowledge_document(
                session,
                document,
                uploaded_by=current_user,
                storage_directory=get_knowledge_storage_directory(),
            )
        except KnowledgeDocumentValidationError as validation_error:
            error = str(validation_error)
        except KnowledgeDocumentPersistenceError as persistence_error:
            return templates.TemplateResponse(
                request=request,
                name="admin_knowledge.html",
                context=_knowledge_context(
                    session,
                    current_user,
                    error=str(persistence_error),
                ),
                status_code=status.HTTP_409_CONFLICT,
                headers={"Cache-Control": "no-store"},
            )
        else:
            try:
                result = process_knowledge_document(
                    session,
                    stored_document,
                    get_knowledge_storage_directory(),
                )
                extraction = result.status
            except KnowledgeDocumentProcessingError:
                extraction = EXTRACTION_PENDING
            indexing = INDEX_PENDING
            if extraction == EXTRACTION_READY:
                try:
                    index_result = index_knowledge_document(
                        session,
                        stored_document,
                        embedding_model,
                    )
                    indexing = index_result.status
                except KnowledgeIndexingError:
                    indexing = INDEX_FAILED
            return RedirectResponse(
                url=(
                    "/app/knowledge?uploaded=true"
                    f"&extraction={extraction}&indexing={indexing}"
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return templates.TemplateResponse(
        request=request,
        name="admin_knowledge.html",
        context=_knowledge_context(session, current_user, error=error),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        headers={"Cache-Control": "no-store"},
    )


@router.post("/app/new-ticket/problem", response_class=HTMLResponse)
def collect_ticket_problem(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
    ai_model: AIModelDependency,
    description: Annotated[str, Form()] = "",
) -> Response:
    """Controlla il racconto iniziale e chiede soltanto gli altri dati essenziali."""

    if redirect := _employee_only(current_user):
        return redirect
    try:
        problem = TicketProblemInput.model_validate({"description": description})
    except ValidationError as error:
        return templates.TemplateResponse(
            request=request,
            name="employee_ticket_intake.html",
            context=_intake_context(
                current_user,
                step="problem",
                values={"description": description[:4_000]},
                errors=_validation_errors(error),
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            headers={"Cache-Control": "no-store"},
        )

    active_sites = _active_sites(session)
    try:
        extraction = extract_ticket_details(
            problem.description,
            available_sites=[
                AvailableSite(id=site.id, code=site.code, name=site.name)
                for site in active_sites
            ],
            ai_model=ai_model,
        )
    except AIModelError:
        extraction = None

    if extraction is not None:
        extracted_values = {
            "description": problem.description,
            "title": extraction.title or "",
            "site_id": extraction.site_id or "",
            "service": extraction.service or "",
            "affected_users": extraction.affected_users or "",
        }
        requested_fields = [field.value for field in extraction.missing_fields]
        if not requested_fields:
            selected_site = next(
                site for site in active_sites if site.id == extraction.site_id
            )
            return templates.TemplateResponse(
                request=request,
                name="employee_ticket_intake.html",
                context=_intake_context(
                    current_user,
                    step="confirmation",
                    values={
                        **extracted_values,
                        "site_name": selected_site.name,
                        "creation_key": secrets.token_urlsafe(32),
                    },
                    requested_fields=[],
                    ai_assisted=True,
                ),
                headers={"Cache-Control": "no-store"},
            )

        return templates.TemplateResponse(
            request=request,
            name="employee_ticket_intake.html",
            context=_intake_context(
                current_user,
                step="details",
                sites=active_sites,
                values=extracted_values,
                requested_fields=requested_fields,
                ai_assisted=True,
            ),
            headers={"Cache-Control": "no-store"},
        )

    return templates.TemplateResponse(
        request=request,
        name="employee_ticket_intake.html",
        context=_intake_context(
            current_user,
            step="details",
            sites=active_sites,
            values={"description": problem.description},
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/app/new-ticket/details", response_class=HTMLResponse)
def collect_ticket_details(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
    description: Annotated[str, Form()] = "",
    title: Annotated[str, Form()] = "",
    site_id: Annotated[str, Form()] = "",
    service: Annotated[str, Form()] = "",
    affected_users: Annotated[str, Form()] = "",
) -> Response:
    """Controlla i dettagli e mostra il riepilogo senza creare il ticket."""

    if redirect := _employee_only(current_user):
        return redirect

    values = {
        "description": description[:4_000],
        "title": title[:120],
        "site_id": site_id,
        "service": service[:100],
        "affected_users": affected_users,
    }
    errors: dict[str, str] = {}
    try:
        problem = TicketProblemInput.model_validate({"description": description})
    except ValidationError as error:
        errors.update(_validation_errors(error))
        problem = None
    clean_site_id = site_id.strip()
    clean_affected_users = affected_users.strip()
    try:
        details = TicketMissingDetailsInput.model_validate(
            {
                "title": title,
                "site_id": (
                    int(clean_site_id) if clean_site_id.isdecimal() else clean_site_id
                ),
                "service": service,
                "affected_users": (
                    int(clean_affected_users)
                    if clean_affected_users.isdecimal()
                    else clean_affected_users
                ),
            }
        )
    except ValidationError as error:
        errors.update(_validation_errors(error))
        details = None

    selected_site = None
    if clean_site_id.isdecimal() and int(clean_site_id) > 0:
        selected_site = session.scalar(
            select(Site).where(
                Site.id == int(clean_site_id),
                Site.is_active.is_(True),
            )
        )
        if selected_site is None:
            errors["site_id"] = INTAKE_ERRORS["site_id"]

    if errors or problem is None or details is None or selected_site is None:
        return templates.TemplateResponse(
            request=request,
            name="employee_ticket_intake.html",
            context=_intake_context(
                current_user,
                step="details",
                sites=_active_sites(session),
                values=values,
                errors=errors,
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            headers={"Cache-Control": "no-store"},
        )

    return templates.TemplateResponse(
        request=request,
        name="employee_ticket_intake.html",
        context=_intake_context(
            current_user,
            step="confirmation",
            values={
                "description": problem.description,
                "title": details.title,
                "site_id": details.site_id,
                "site_name": selected_site.name,
                "service": details.service,
                "affected_users": details.affected_users,
                "creation_key": secrets.token_urlsafe(32),
            },
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/app/new-ticket/edit", response_class=HTMLResponse)
def edit_ticket_draft(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
    description: Annotated[str, Form()] = "",
    title: Annotated[str, Form()] = "",
    site_id: Annotated[str, Form()] = "",
    service: Annotated[str, Form()] = "",
    affected_users: Annotated[str, Form()] = "",
) -> Response:
    """Riapre i campi raccolti per permettere una correzione."""

    if redirect := _employee_only(current_user):
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="employee_ticket_intake.html",
        context=_intake_context(
            current_user,
            step="details",
            sites=_active_sites(session),
            values={
                "description": description[:4_000],
                "title": title[:120],
                "site_id": site_id,
                "service": service[:100],
                "affected_users": affected_users,
            },
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/app/new-ticket/confirm")
def confirm_ticket_draft(
    request: Request,
    session: DatabaseSession,
    current_user: WebUser,
    ai_model: AIModelDependency,
    description: Annotated[str, Form()] = "",
    title: Annotated[str, Form()] = "",
    site_id: Annotated[str, Form()] = "",
    service: Annotated[str, Form()] = "",
    affected_users: Annotated[str, Form()] = "",
    creation_key: Annotated[str, Form()] = "",
    confirmed: Annotated[str, Form()] = "",
) -> Response:
    """Crea il ticket soltanto dopo una conferma positiva e validata."""

    if redirect := _employee_only(current_user):
        return redirect

    clean_site_id = site_id.strip()
    clean_affected_users = affected_users.strip()
    raw_values = {
        "description": description,
        "title": title,
        "site_id": int(clean_site_id) if clean_site_id.isdecimal() else clean_site_id,
        "service": service,
        "affected_users": (
            int(clean_affected_users)
            if clean_affected_users.isdecimal()
            else clean_affected_users
        ),
        "confirmed": confirmed == "true",
    }
    errors: dict[str, str] = {}
    try:
        payload = TicketCreate.model_validate(raw_values)
    except ValidationError as error:
        errors.update(_validation_errors(error))
        if any(item["loc"] and item["loc"][0] == "confirmed" for item in error.errors()):
            errors["confirmation"] = "La richiesta deve essere confermata esplicitamente."
        payload = None
    try:
        validated_key = TicketCreationKeyInput.model_validate(
            {"creation_key": creation_key}
        ).creation_key
    except ValidationError:
        errors["confirmation"] = "Il riepilogo non è più valido. Rivedi i dati e riprova."
        validated_key = None

    selected_site = None
    if clean_site_id.isdecimal() and int(clean_site_id) > 0:
        selected_site = session.scalar(
            select(Site).where(
                Site.id == int(clean_site_id),
                Site.is_active.is_(True),
            )
        )
        if selected_site is None:
            errors["site_id"] = INTAKE_ERRORS["site_id"]

    if errors or payload is None or validated_key is None or selected_site is None:
        return templates.TemplateResponse(
            request=request,
            name="employee_ticket_intake.html",
            context=_intake_context(
                current_user,
                step="details",
                sites=_active_sites(session),
                values={
                    "description": description[:4_000],
                    "title": title[:120],
                    "site_id": site_id,
                    "service": service[:100],
                    "affected_users": affected_users,
                },
                errors=errors,
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            headers={"Cache-Control": "no-store"},
        )

    try:
        ticket = create_confirmed_ticket(
            session,
            payload,
            current_user,
            creation_key=validated_key,
        )
    except (TicketSiteNotFoundError, TicketPersistenceError):
        return templates.TemplateResponse(
            request=request,
            name="employee_ticket_intake.html",
            context=_intake_context(
                current_user,
                step="confirmation",
                values={
                    **payload.model_dump(exclude={"confirmed"}),
                    "site_name": selected_site.name,
                    "creation_key": validated_key,
                },
                errors={
                    "confirmation": (
                        "Non siamo riusciti a creare il ticket. Riprova tra poco."
                    )
                },
            ),
            status_code=status.HTTP_409_CONFLICT,
            headers={"Cache-Control": "no-store"},
        )

    try:
        ticket = classify_confirmed_ticket(session, ticket, ai_model=ai_model)
    except (AIModelError, TicketClassificationPersistenceError):
        pass

    return RedirectResponse(
        url=f"/app/tickets/{ticket.id}?created=true",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/app/tickets/{ticket_id}", response_class=HTMLResponse)
def employee_ticket_detail(
    request: Request,
    ticket_id: WebTicketId,
    session: DatabaseSession,
    current_user: WebUser,
    created: Annotated[bool, Query()] = False,
    updated: Annotated[bool, Query()] = False,
    classification_reviewed: Annotated[bool, Query()] = False,
    solution_attempted: Annotated[bool, Query()] = False,
    action_result: Annotated[str | None, Query()] = None,
) -> Response:
    """Mostra il dettaglio personale o gli strumenti riservati al tecnico."""

    if current_user.role is not Role.EMPLOYEE:
        ticket = get_visible_ticket(session, current_user, ticket_id)
        if ticket is None:
            return templates.TemplateResponse(
                request=request,
                name="technician_ticket_not_found.html",
                context=_workspace_context(current_user, "Ticket non trovato"),
                status_code=status.HTTP_404_NOT_FOUND,
                headers={"Cache-Control": "no-store"},
            )
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_detail.html",
            context=_technical_ticket_context(
                session,
                current_user,
                ticket,
                updated=updated,
                classification_reviewed=classification_reviewed,
                solution_attempted=solution_attempted,
                action_result=action_result,
            ),
            headers={"Cache-Control": "no-store"},
        )

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
    context["created"] = created
    return templates.TemplateResponse(
        request=request,
        name="employee_ticket_detail.html",
        context=context,
        headers={"Cache-Control": "no-store"},
    )


@router.post(
    "/app/tickets/{ticket_id}/suggest-solution",
    response_class=HTMLResponse,
)
def suggest_technical_ticket_solution(
    request: Request,
    ticket_id: WebTicketId,
    session: DatabaseSession,
    current_user: WebUser,
    ai_model: AIModelDependency,
    embedding_model: EmbeddingModelDependency,
) -> Response:
    """Genera su richiesta un suggerimento e conserva le fonti realmente usate."""

    if current_user.role not in {Role.TECHNICIAN, Role.ADMIN}:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_not_found.html",
            context=_workspace_context(current_user, "Ticket non trovato"),
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"Cache-Control": "no-store"},
        )

    try:
        generate_ticket_solution(
            session,
            ticket,
            ai_model=ai_model,
            embedding_model=embedding_model,
        )
    except TicketSolutionPersistenceError:
        session.rollback()
        ticket = session.get(Ticket, ticket_id)
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_detail.html",
            context=_technical_ticket_context(
                session,
                current_user,
                ticket,
                solution_attempted=True,
                solution_error=(
                    "Non siamo riusciti a salvare il suggerimento e le sue fonti. "
                    "Il ticket non è stato modificato."
                ),
            ),
            status_code=status.HTTP_409_CONFLICT,
            headers={"Cache-Control": "no-store"},
        )

    return RedirectResponse(
        url=f"/app/tickets/{ticket_id}?solution_attempted=true",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post(
    "/app/tickets/{ticket_id}/actions/{action_id}/decision",
    response_class=HTMLResponse,
)
def decide_technical_action(
    request: Request,
    ticket_id: WebTicketId,
    action_id: Annotated[
        int,
        PathParameter(gt=0, description="Identificativo positivo della proposta"),
    ],
    session: DatabaseSession,
    current_user: WebUser,
    service_client: ActionServiceClientDependency,
    decision: Annotated[ActionDecision, Form()],
) -> Response:
    """Approva o rifiuta una proposta e chiama il simulatore solo se approvata."""

    if current_user.role not in {Role.TECHNICIAN, Role.ADMIN}:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_not_found.html",
            context=_workspace_context(current_user, "Ticket non trovato"),
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"Cache-Control": "no-store"},
        )

    try:
        result = decide_action_proposal(
            session,
            ticket_id=ticket_id,
            action_id=action_id,
            reviewer=current_user,
            decision=decision,
            service_client=service_client,
        )
    except ActionNotFoundError:
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_not_found.html",
            context=_workspace_context(current_user, "Azione non trovata"),
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"Cache-Control": "no-store"},
        )
    except ActionAlreadyDecidedError:
        return RedirectResponse(
            url=f"/app/tickets/{ticket_id}?action_result=already_decided",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except (ActionProposalDataError, ActionDecisionPersistenceError):
        session.rollback()
        ticket = session.get(Ticket, ticket_id)
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_detail.html",
            context=_technical_ticket_context(
                session,
                current_user,
                ticket,
                action_error=(
                    "Non siamo riusciti a completare la decisione in modo sicuro. "
                    "Nessuna nuova chiamata verrà ripetuta automaticamente."
                ),
            ),
            status_code=status.HTTP_409_CONFLICT,
            headers={"Cache-Control": "no-store"},
        )

    return RedirectResponse(
        url=f"/app/tickets/{ticket_id}?action_result={result.status.value}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/app/tickets/{ticket_id}/update", response_class=HTMLResponse)
def update_technical_ticket(
    request: Request,
    ticket_id: WebTicketId,
    session: DatabaseSession,
    current_user: WebUser,
    status_value: Annotated[str, Form(alias="status")] = "",
    assigned_technician_id: Annotated[str, Form()] = "",
    assigned_group: Annotated[str, Form()] = "",
    category: Annotated[str, Form()] = "",
    subcategory: Annotated[str, Form()] = "",
    impact: Annotated[str, Form()] = "",
    urgency: Annotated[str, Form()] = "",
    technician_note: Annotated[str, Form()] = "",
    resolution: Annotated[str, Form()] = "",
    review_classification: Annotated[str, Form()] = "",
) -> Response:
    """Controlla e salva assegnazione, classificazione e avanzamento manuali."""

    if current_user.role not in {Role.TECHNICIAN, Role.ADMIN}:
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_not_found.html",
            context=_workspace_context(current_user, "Ticket non trovato"),
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"Cache-Control": "no-store"},
        )

    payload, values, errors = _technical_update_payload(
        status_value=status_value,
        assigned_technician_id=assigned_technician_id,
        assigned_group=assigned_group,
        category=category,
        subcategory=subcategory,
        impact=impact,
        urgency=urgency,
        technician_note=technician_note,
        resolution=resolution,
        review_classification=review_classification == "true",
    )
    if payload is None:
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_detail.html",
            context=_technical_ticket_context(
                session,
                current_user,
                ticket,
                values=values,
                errors=errors,
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            headers={"Cache-Control": "no-store"},
        )

    try:
        update_managed_ticket(
            session,
            ticket_id,
            payload,
            updated_by=current_user,
        )
    except ManagedTicketNotFoundError:
        return templates.TemplateResponse(
            request=request,
            name="technician_ticket_not_found.html",
            context=_workspace_context(current_user, "Ticket non trovato"),
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"Cache-Control": "no-store"},
        )
    except (ManagedTechnicianNotFoundError, ManagedTechnicianUnavailableError):
        errors["assigned_technician_id"] = "Seleziona un tecnico attivo."
    except InvalidStatusTransitionError:
        errors["status"] = "Questo passaggio di stato non è consentito."
    except ResolutionRequiredError:
        errors["resolution"] = "Scrivi la soluzione prima di risolvere o chiudere."
    except ClassificationReviewRequiredError:
        errors["classification"] = (
            "Completa la classificazione prima di confermare la revisione."
        )
    except TicketUpdatePersistenceError:
        errors["update"] = "Non siamo riusciti a salvare. Riprova tra poco."
    else:
        result_query = (
            "classification_reviewed=true"
            if review_classification == "true"
            else "updated=true"
        )
        return RedirectResponse(
            url=f"/app/tickets/{ticket_id}?{result_query}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    session.rollback()
    ticket = session.get(Ticket, ticket_id)
    return templates.TemplateResponse(
        request=request,
        name="technician_ticket_detail.html",
        context=_technical_ticket_context(
            session,
            current_user,
            ticket,
            values=values,
            errors=errors,
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
