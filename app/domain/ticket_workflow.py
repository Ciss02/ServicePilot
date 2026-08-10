"""Regole deterministiche per il ciclo di vita dei ticket."""

from app.domain.vocabulary import TicketStatus


ALLOWED_STATUS_TRANSITIONS: dict[TicketStatus, frozenset[TicketStatus]] = {
    TicketStatus.NEW: frozenset({TicketStatus.IN_PROGRESS}),
    TicketStatus.IN_PROGRESS: frozenset(
        {
            TicketStatus.WAITING_FOR_REQUESTER,
            TicketStatus.WAITING_FOR_VENDOR,
            TicketStatus.RESOLVED,
        }
    ),
    TicketStatus.WAITING_FOR_REQUESTER: frozenset(
        {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED}
    ),
    TicketStatus.WAITING_FOR_VENDOR: frozenset(
        {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED}
    ),
    TicketStatus.RESOLVED: frozenset(
        {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED}
    ),
    TicketStatus.CLOSED: frozenset(),
}


def can_transition_status(current: TicketStatus, target: TicketStatus) -> bool:
    """Indica se il cambio di stato segue il flusso tecnico approvato."""

    if not isinstance(current, TicketStatus):
        raise TypeError("current deve essere un valore TicketStatus")
    if not isinstance(target, TicketStatus):
        raise TypeError("target deve essere un valore TicketStatus")

    if current is target:
        return True
    return target in ALLOWED_STATUS_TRANSITIONS[current]
