"""Query condivise che applicano la visibilità dei ticket nel backend."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import Ticket, User
from app.domain.vocabulary import Role


def visible_tickets_query(current_user: User) -> Select[tuple[Ticket]]:
    """Costruisce la query visibile al ruolo, filtrando sempre il dipendente."""

    query = select(Ticket)
    if current_user.role is Role.EMPLOYEE:
        query = query.where(Ticket.requester_id == current_user.id)
    return query


def list_visible_tickets(session: Session, current_user: User) -> list[Ticket]:
    """Restituisce i ticket autorizzati, dal più recente."""

    query = visible_tickets_query(current_user).order_by(Ticket.created_at.desc(), Ticket.id.desc())
    return list(session.scalars(query).all())


def get_visible_ticket(
    session: Session,
    current_user: User,
    ticket_id: int,
) -> Ticket | None:
    """Restituisce un ticket soltanto quando è visibile all'utente corrente."""

    query = visible_tickets_query(current_user).where(Ticket.id == ticket_id)
    return session.scalar(query)
