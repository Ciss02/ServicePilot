"""Creazione e lettura controllata degli eventi di audit."""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, ProposedAction, Ticket, User
from app.domain.vocabulary import (
    ActionDecision,
    ActionStatus,
    AuditActorType,
    AuditEventType,
    ClassificationReviewStatus,
)

MAX_AUDIT_DETAILS_LENGTH = 4_000


def _value(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    return value


def _details_json(details: dict[str, object]) -> str:
    """Serializza soltanto dettagli costruiti internamente e di dimensione limitata."""

    encoded = json.dumps(details, ensure_ascii=False, sort_keys=True)
    if len(encoded) > MAX_AUDIT_DETAILS_LENGTH:
        raise ValueError("I dettagli dell'evento di audit sono troppo estesi")
    return encoded


def _append_event(
    session: Session,
    *,
    ticket_id: int,
    actor_type: AuditActorType,
    event_type: AuditEventType,
    summary: str,
    details: dict[str, object] | None = None,
    actor_user_id: int | None = None,
    action_id: int | None = None,
    event_key: str | None = None,
    created_at: datetime | None = None,
) -> AuditEvent:
    event = AuditEvent(
        ticket_id=ticket_id,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        event_type=event_type,
        summary=summary,
        details_json=_details_json(details or {}),
        action_id=action_id,
        event_key=event_key,
    )
    if created_at is not None:
        event.created_at = created_at
    session.add(event)
    return event


@dataclass(frozen=True)
class TicketAuditSnapshot:
    """Fotografia dei soli campi necessari a descrivere una modifica."""

    site_id: int
    service: str
    affected_users: int
    category: object
    subcategory: str | None
    impact: object
    urgency: object
    priority: object
    assigned_group: str | None
    assigned_technician_id: int | None
    status: object
    technician_note: str | None
    resolution: str | None
    classification_review_status: object

    @classmethod
    def capture(cls, ticket: Ticket) -> "TicketAuditSnapshot":
        return cls(
            site_id=ticket.site_id,
            service=ticket.service,
            affected_users=ticket.affected_users,
            category=ticket.category,
            subcategory=ticket.subcategory,
            impact=ticket.impact,
            urgency=ticket.urgency,
            priority=ticket.priority,
            assigned_group=ticket.assigned_group,
            assigned_technician_id=ticket.assigned_technician_id,
            status=ticket.status,
            technician_note=ticket.technician_note,
            resolution=ticket.resolution,
            classification_review_status=ticket.classification_review_status,
        )


def record_ticket_created(
    session: Session,
    ticket: Ticket,
    requester: User,
    *,
    event_key: str | None = None,
    created_at: datetime | None = None,
) -> AuditEvent:
    return _append_event(
        session,
        ticket_id=ticket.id,
        actor_type=AuditActorType.HUMAN,
        actor_user_id=requester.id,
        event_type=AuditEventType.TICKET_CREATED,
        summary="Ticket creato e confermato",
        details={"status": ticket.status.value, "site_id": ticket.site_id},
        event_key=event_key,
        created_at=created_at,
    )


def record_ai_classification_result(session: Session, ticket: Ticket) -> AuditEvent:
    status = ticket.classification_review_status
    if status is ClassificationReviewStatus.AI_SUGGESTED:
        return _append_event(
            session,
            ticket_id=ticket.id,
            actor_type=AuditActorType.AI,
            event_type=AuditEventType.AI_CLASSIFICATION_SUGGESTED,
            summary="Classificazione proposta dall'assistente AI",
            details={
                "category": _value(ticket.category),
                "impact": _value(ticket.impact),
                "urgency": _value(ticket.urgency),
                "priority": _value(ticket.priority),
                "assigned_group": ticket.assigned_group,
            },
        )
    if status is ClassificationReviewStatus.AI_INVALID_RESPONSE:
        event_type = AuditEventType.AI_CLASSIFICATION_INVALID
        summary = "Classificazione AI non utilizzabile"
    else:
        event_type = AuditEventType.AI_CLASSIFICATION_UNAVAILABLE
        summary = "Classificazione AI non disponibile"
    return _append_event(
        session,
        ticket_id=ticket.id,
        actor_type=AuditActorType.AI,
        event_type=event_type,
        summary=summary,
        details={"result": status.value},
    )


def record_ticket_update_events(
    session: Session,
    ticket: Ticket,
    *,
    before: TicketAuditSnapshot,
    actor: User,
) -> list[AuditEvent]:
    """Aggiunge uno o più eventi leggibili per le modifiche realmente avvenute."""

    events: list[AuditEvent] = []
    if before.status != ticket.status:
        events.append(
            _append_event(
                session,
                ticket_id=ticket.id,
                actor_type=AuditActorType.HUMAN,
                actor_user_id=actor.id,
                event_type=AuditEventType.TICKET_STATUS_CHANGED,
                summary="Stato del ticket aggiornato",
                details={
                    "from_status": _value(before.status),
                    "to_status": _value(ticket.status),
                },
            )
        )

    if (
        before.assigned_group != ticket.assigned_group
        or before.assigned_technician_id != ticket.assigned_technician_id
    ):
        events.append(
            _append_event(
                session,
                ticket_id=ticket.id,
                actor_type=AuditActorType.HUMAN,
                actor_user_id=actor.id,
                event_type=AuditEventType.TICKET_ASSIGNMENT_CHANGED,
                summary="Assegnazione del ticket aggiornata",
                details={
                    "from_group": before.assigned_group,
                    "to_group": ticket.assigned_group,
                    "from_technician_id": before.assigned_technician_id,
                    "to_technician_id": ticket.assigned_technician_id,
                },
            )
        )

    classification_before = (
        before.category,
        before.subcategory,
        before.impact,
        before.urgency,
        before.priority,
        before.classification_review_status,
    )
    classification_after = (
        ticket.category,
        ticket.subcategory,
        ticket.impact,
        ticket.urgency,
        ticket.priority,
        ticket.classification_review_status,
    )
    classification_changed = classification_before != classification_after
    classification_reviewed = (
        classification_changed
        and ticket.classification_review_status is ClassificationReviewStatus.HUMAN_REVIEWED
    )
    if classification_reviewed:
        events.append(
            _append_event(
                session,
                ticket_id=ticket.id,
                actor_type=AuditActorType.HUMAN,
                actor_user_id=actor.id,
                event_type=AuditEventType.CLASSIFICATION_REVIEWED,
                summary="Classificazione verificata da una persona",
                details={
                    "category": _value(ticket.category),
                    "impact": _value(ticket.impact),
                    "urgency": _value(ticket.urgency),
                    "priority": _value(ticket.priority),
                },
            )
        )

    other_fields = {
        "classification": classification_changed and not classification_reviewed,
        "site": before.site_id != ticket.site_id,
        "service": before.service != ticket.service,
        "affected_users": before.affected_users != ticket.affected_users,
        "technician_note": before.technician_note != ticket.technician_note,
        "resolution": before.resolution != ticket.resolution,
    }
    changed_fields = [name for name, changed in other_fields.items() if changed]
    if changed_fields:
        events.append(
            _append_event(
                session,
                ticket_id=ticket.id,
                actor_type=AuditActorType.HUMAN,
                actor_user_id=actor.id,
                event_type=AuditEventType.TICKET_UPDATED,
                summary="Dettagli operativi del ticket aggiornati",
                details={"changed_fields": changed_fields},
            )
        )
    return events


def record_ai_solution_result(
    session: Session,
    ticket: Ticket,
    *,
    source_count: int = 0,
) -> AuditEvent:
    if ticket.ai_solution_status == "generated":
        event_type = AuditEventType.AI_SOLUTION_GENERATED
        summary = "Suggerimento AI generato con fonti"
    elif ticket.ai_solution_status == "invalid_response":
        event_type = AuditEventType.AI_SOLUTION_INVALID
        summary = "Suggerimento AI non utilizzabile"
    else:
        event_type = AuditEventType.AI_SOLUTION_UNAVAILABLE
        summary = "Suggerimento AI non disponibile"
    return _append_event(
        session,
        ticket_id=ticket.id,
        actor_type=AuditActorType.AI,
        event_type=event_type,
        summary=summary,
        details={
            "result": ticket.ai_solution_status,
            "source_count": source_count,
        },
    )


def record_action_proposed(
    session: Session,
    action: ProposedAction,
    *,
    event_key: str | None = None,
    created_at: datetime | None = None,
) -> AuditEvent:
    return _append_event(
        session,
        ticket_id=action.ticket_id,
        actor_type=AuditActorType.AI,
        event_type=AuditEventType.ACTION_PROPOSED,
        summary="Nuova azione proposta dall'assistente",
        details={"action_type": action.action_type.value},
        action_id=action.id,
        event_key=event_key,
        created_at=created_at,
    )


def record_action_decision(
    session: Session,
    action: ProposedAction,
    *,
    reviewer: User,
    decision: ActionDecision,
) -> AuditEvent:
    approved = decision is ActionDecision.APPROVE
    return _append_event(
        session,
        ticket_id=action.ticket_id,
        actor_type=AuditActorType.HUMAN,
        actor_user_id=reviewer.id,
        event_type=(AuditEventType.ACTION_APPROVED if approved else AuditEventType.ACTION_REJECTED),
        summary="Azione proposta approvata" if approved else "Azione proposta rifiutata",
        details={
            "action_type": action.action_type.value,
            "decision": decision.value,
        },
        action_id=action.id,
    )


def record_action_execution_started(
    session: Session,
    action: ProposedAction,
) -> AuditEvent:
    return _append_event(
        session,
        ticket_id=action.ticket_id,
        actor_type=AuditActorType.SYSTEM,
        event_type=AuditEventType.ACTION_EXECUTION_STARTED,
        summary="Esecuzione simulata avviata",
        details={"action_type": action.action_type.value},
        action_id=action.id,
    )


def record_action_execution_result(
    session: Session,
    action: ProposedAction,
) -> AuditEvent:
    succeeded = action.status is ActionStatus.SUCCEEDED
    return _append_event(
        session,
        ticket_id=action.ticket_id,
        actor_type=AuditActorType.SYSTEM,
        event_type=(
            AuditEventType.ACTION_EXECUTION_SUCCEEDED
            if succeeded
            else AuditEventType.ACTION_EXECUTION_FAILED
        ),
        summary=("Azione simulata completata" if succeeded else "Azione simulata non riuscita"),
        details={
            "action_type": action.action_type.value,
            "reference": action.execution_reference,
            "error_code": action.execution_error_code,
        },
        action_id=action.id,
    )


def list_ticket_audit_events(session: Session, ticket_id: int) -> list[AuditEvent]:
    return list(
        session.scalars(
            select(AuditEvent)
            .where(AuditEvent.ticket_id == ticket_id)
            .order_by(AuditEvent.created_at, AuditEvent.id)
        ).all()
    )


def list_audit_events(
    session: Session,
    *,
    actor_type: AuditActorType | None = None,
    ticket_id: int | None = None,
    limit: int = 100,
) -> list[AuditEvent]:
    statement = select(AuditEvent)
    if actor_type is not None:
        statement = statement.where(AuditEvent.actor_type == actor_type)
    if ticket_id is not None:
        statement = statement.where(AuditEvent.ticket_id == ticket_id)
    return list(
        session.scalars(
            statement.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit)
        ).all()
    )
