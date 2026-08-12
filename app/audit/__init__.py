"""Registro append-only delle operazioni rilevanti di ServicePilot."""

from app.audit.events import (
    TicketAuditSnapshot,
    list_audit_events,
    list_ticket_audit_events,
    record_action_decision,
    record_action_execution_result,
    record_action_execution_started,
    record_action_proposed,
    record_ai_classification_result,
    record_ai_solution_result,
    record_ticket_created,
    record_ticket_update_events,
)
from app.audit.presentation import AuditEventView, present_audit_events

__all__ = [
    "AuditEventView",
    "TicketAuditSnapshot",
    "list_audit_events",
    "list_ticket_audit_events",
    "present_audit_events",
    "record_action_decision",
    "record_action_execution_result",
    "record_action_execution_started",
    "record_action_proposed",
    "record_ai_classification_result",
    "record_ai_solution_result",
    "record_ticket_created",
    "record_ticket_update_events",
]
