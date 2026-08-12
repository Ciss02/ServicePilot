"""Concetti e regole condivisi del dominio ServicePilot."""

from app.domain.action_contracts import (
    ActionProposalCreate,
    ActionProposalRead,
    AssignmentActionPayload,
    RequesterCommunicationPayload,
    VendorEscalationPayload,
)
from app.domain.priority import calculate_priority
from app.domain.ticket_contracts import (
    TicketClassification,
    TicketCreate,
    TicketRead,
    TicketUpdate,
)
from app.domain.ticket_workflow import ALLOWED_STATUS_TRANSITIONS, can_transition_status
from app.domain.vocabulary import (
    ActionDecision,
    ActionStatus,
    ActionType,
    AuditActorType,
    AuditEventType,
    Impact,
    Priority,
    Role,
    TicketCategory,
    TicketStatus,
    Urgency,
)

__all__ = [
    "ActionProposalCreate",
    "ActionProposalRead",
    "ActionDecision",
    "ActionStatus",
    "ActionType",
    "AuditActorType",
    "AuditEventType",
    "AssignmentActionPayload",
    "Impact",
    "ALLOWED_STATUS_TRANSITIONS",
    "Priority",
    "RequesterCommunicationPayload",
    "Role",
    "TicketCategory",
    "TicketClassification",
    "TicketCreate",
    "TicketRead",
    "TicketStatus",
    "TicketUpdate",
    "Urgency",
    "VendorEscalationPayload",
    "calculate_priority",
    "can_transition_status",
]
