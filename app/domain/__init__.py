"""Concetti e regole condivisi del dominio ServicePilot."""

from app.domain.vocabulary import (
    Impact,
    Priority,
    Role,
    TicketCategory,
    TicketStatus,
    Urgency,
)
from app.domain.priority import calculate_priority
from app.domain.ticket_contracts import (
    TicketClassification,
    TicketCreate,
    TicketRead,
    TicketUpdate,
)

__all__ = [
    "Impact",
    "Priority",
    "Role",
    "TicketCategory",
    "TicketClassification",
    "TicketCreate",
    "TicketRead",
    "TicketStatus",
    "TicketUpdate",
    "Urgency",
    "calculate_priority",
]
