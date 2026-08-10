"""API essenziali per creare, leggere e gestire i ticket."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Site, Ticket, User
from app.db.session import get_session
from app.domain.ticket_contracts import TicketCreate, TicketRead, TicketUpdate
from app.domain.ticket_workflow import can_transition_status
from app.domain.vocabulary import Role, TicketStatus


router = APIRouter(prefix="/tickets", tags=["ticket"])
DatabaseSession = Annotated[Session, Depends(get_session)]
TicketId = Annotated[int, Path(gt=0, description="Identificativo positivo del ticket")]


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un ticket confermato",
)
def create_ticket(payload: TicketCreate, session: DatabaseSession) -> Ticket:
    """Salva una richiesta confermata collegata a utente e sede esistenti."""

    if session.get(User, payload.requester_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Richiedente {payload.requester_id} non trovato",
        )
    if session.get(Site, payload.site_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede {payload.site_id} non trovata",
        )

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        requester_id=payload.requester_id,
        site_id=payload.site_id,
        service=payload.service,
        affected_users=payload.affected_users,
    )
    session.add(ticket)
    try:
        session.commit()
        session.refresh(ticket)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Il ticket non può essere salvato con i riferimenti forniti",
        ) from error
    return ticket


@router.get(
    "",
    response_model=list[TicketRead],
    summary="Elenca i ticket",
)
def list_tickets(session: DatabaseSession) -> list[Ticket]:
    """Restituisce tutti i ticket, dal più recente."""

    query = select(Ticket).order_by(Ticket.created_at.desc(), Ticket.id.desc())
    return list(session.scalars(query).all())


@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Legge un ticket",
)
def get_ticket(ticket_id: TicketId, session: DatabaseSession) -> Ticket:
    """Restituisce il ticket richiesto o un errore chiaro."""

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} non trovato",
        )
    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Aggiorna la gestione tecnica di un ticket",
)
def update_ticket(
    ticket_id: TicketId,
    payload: TicketUpdate,
    session: DatabaseSession,
) -> Ticket:
    """Modifica soltanto i campi tecnici validati e salva tutto insieme."""

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} non trovato",
        )

    if payload.site_id is not None and session.get(Site, payload.site_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede {payload.site_id} non trovata",
        )

    if payload.assigned_technician_id is not None:
        technician = session.get(User, payload.assigned_technician_id)
        if technician is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tecnico {payload.assigned_technician_id} non trovato",
            )
        if (
            technician.role not in {Role.TECHNICIAN, Role.ADMIN}
            or not technician.is_active
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Il ticket può essere assegnato soltanto a un tecnico attivo",
            )

    if payload.status is not None:
        if not can_transition_status(ticket.status, payload.status):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Transizione da {ticket.status.value} a "
                    f"{payload.status.value} non consentita"
                ),
            )
        future_resolution = payload.resolution or ticket.resolution
        if (
            payload.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}
            and not future_resolution
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Per risolvere o chiudere il ticket è necessaria una soluzione",
            )

    update_values = payload.model_dump(exclude_unset=True, exclude={"classification"})
    for field_name, value in update_values.items():
        setattr(ticket, field_name, value)

    if payload.classification is not None:
        ticket.category = payload.classification.category
        ticket.subcategory = payload.classification.subcategory
        ticket.impact = payload.classification.impact
        ticket.urgency = payload.classification.urgency
        ticket.priority = payload.classification.priority

    try:
        session.commit()
        session.refresh(ticket)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Il ticket non può essere aggiornato con i riferimenti forniti",
        ) from error
    return ticket
