"""Operazioni condivise per la gestione tecnica dei ticket."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Site, Ticket, User
from app.domain.ticket_contracts import TicketUpdate
from app.domain.ticket_workflow import can_transition_status
from app.domain.vocabulary import ClassificationReviewStatus, Role, TicketStatus


class TicketManagementError(Exception):
    """Errore atteso durante un aggiornamento tecnico."""


class ManagedTicketNotFoundError(TicketManagementError):
    """Il ticket richiesto non esiste."""


class ManagedSiteNotFoundError(TicketManagementError):
    """La sede richiesta non esiste."""


class ManagedTechnicianNotFoundError(TicketManagementError):
    """Il tecnico richiesto non esiste."""


class ManagedTechnicianUnavailableError(TicketManagementError):
    """L'account indicato non può ricevere ticket."""


class InvalidStatusTransitionError(TicketManagementError):
    """Il cambio di stato non segue il flusso consentito."""

    def __init__(self, current: TicketStatus, target: TicketStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(current, target)


class ResolutionRequiredError(TicketManagementError):
    """La chiusura richiede una soluzione leggibile."""


class TicketUpdatePersistenceError(TicketManagementError):
    """Il database non ha potuto salvare l'aggiornamento."""


class ClassificationReviewRequiredError(TicketManagementError):
    """La conferma umana richiede una classificazione completa."""


def update_managed_ticket(
    session: Session,
    ticket_id: int,
    payload: TicketUpdate,
) -> Ticket:
    """Controlla e salva in modo atomico un aggiornamento tecnico."""

    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise ManagedTicketNotFoundError

    if payload.site_id is not None and session.get(Site, payload.site_id) is None:
        raise ManagedSiteNotFoundError

    if payload.assigned_technician_id is not None:
        technician = session.get(User, payload.assigned_technician_id)
        if technician is None:
            raise ManagedTechnicianNotFoundError
        if (
            technician.role not in {Role.TECHNICIAN, Role.ADMIN}
            or not technician.is_active
        ):
            raise ManagedTechnicianUnavailableError

    if payload.status is not None:
        if not can_transition_status(ticket.status, payload.status):
            raise InvalidStatusTransitionError(ticket.status, payload.status)
        future_resolution = payload.resolution or ticket.resolution
        if (
            payload.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}
            and not future_resolution
        ):
            raise ResolutionRequiredError

    update_values = payload.model_dump(
        exclude_unset=True,
        exclude={"classification", "classification_reviewed"},
    )
    for field_name, value in update_values.items():
        setattr(ticket, field_name, value)

    if payload.classification is not None:
        ticket.category = payload.classification.category
        ticket.subcategory = payload.classification.subcategory
        ticket.impact = payload.classification.impact
        ticket.urgency = payload.classification.urgency
        ticket.priority = payload.classification.priority

    if payload.classification_reviewed:
        if not all(
            value is not None
            for value in (ticket.category, ticket.impact, ticket.urgency, ticket.priority)
        ):
            raise ClassificationReviewRequiredError
        ticket.classification_review_status = (
            ClassificationReviewStatus.HUMAN_REVIEWED
        )

    try:
        session.commit()
        session.refresh(ticket)
    except IntegrityError as error:
        session.rollback()
        raise TicketUpdatePersistenceError from error
    return ticket
