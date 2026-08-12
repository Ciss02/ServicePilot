"""Creazione condivisa e ripetibile dei ticket confermati."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import record_ticket_created
from app.db.models import Site, Ticket, User
from app.domain.ticket_contracts import TicketCreate


class TicketSiteNotFoundError(Exception):
    """La sede indicata non esiste."""


class TicketPersistenceError(Exception):
    """Il ticket non puo essere salvato con i riferimenti indicati."""


def create_confirmed_ticket(
    session: Session,
    payload: TicketCreate,
    requester: User,
    *,
    creation_key: str | None = None,
) -> Ticket:
    """Salva una richiesta confermata o restituisce quella gia creata."""

    if creation_key:
        existing_ticket = session.scalar(
            select(Ticket).where(
                Ticket.creation_key == creation_key,
                Ticket.requester_id == requester.id,
            )
        )
        if existing_ticket is not None:
            return existing_ticket

    if session.get(Site, payload.site_id) is None:
        raise TicketSiteNotFoundError

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        requester_id=requester.id,
        site_id=payload.site_id,
        service=payload.service,
        affected_users=payload.affected_users,
        creation_key=creation_key,
    )
    session.add(ticket)
    try:
        session.flush()
        record_ticket_created(session, ticket, requester)
        session.commit()
        session.refresh(ticket)
    except IntegrityError as error:
        session.rollback()
        if creation_key:
            existing_ticket = session.scalar(
                select(Ticket).where(
                    Ticket.creation_key == creation_key,
                    Ticket.requester_id == requester.id,
                )
            )
            if existing_ticket is not None:
                return existing_ticket
        raise TicketPersistenceError from error
    return ticket
