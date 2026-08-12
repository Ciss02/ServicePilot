"""Converte le azioni proposte in contenuti leggibili nella pagina tecnica."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.actions import list_action_proposals
from app.db.models import User
from app.domain.action_contracts import (
    AssignmentActionPayload,
    RequesterCommunicationPayload,
    VendorEscalationPayload,
)
from app.domain.vocabulary import ActionStatus, ActionType


ACTION_TYPE_LABELS = {
    ActionType.ASSIGN_TICKET: "Assegnazione del ticket",
    ActionType.NOTIFY_REQUESTER: "Comunicazione al richiedente",
    ActionType.ESCALATE_VENDOR: "Escalation al fornitore",
}
ACTION_STATUS_LABELS = {
    ActionStatus.PENDING_APPROVAL: "In attesa di approvazione",
    ActionStatus.APPROVED: "Approvata",
    ActionStatus.REJECTED: "Rifiutata",
    ActionStatus.EXECUTING: "In esecuzione",
    ActionStatus.SUCCEEDED: "Completata",
    ActionStatus.FAILED: "Non riuscita",
}
ACTION_STATUS_CLASSES = {
    ActionStatus.PENDING_APPROVAL: "pending",
    ActionStatus.APPROVED: "approved",
    ActionStatus.REJECTED: "rejected",
    ActionStatus.EXECUTING: "executing",
    ActionStatus.SUCCEEDED: "succeeded",
    ActionStatus.FAILED: "failed",
}


@dataclass(frozen=True)
class ActionPayloadItem:
    label: str
    value: str


@dataclass(frozen=True)
class ProposedActionView:
    id: int
    type_label: str
    status_label: str
    status_class: str
    rationale: str
    expected_effect: str
    payload_items: tuple[ActionPayloadItem, ...]
    can_decide: bool
    reviewer_name: str
    decided_at: str
    execution_reference: str
    execution_message: str


def _format_datetime(value: datetime | None) -> str:
    return value.strftime("%d/%m/%Y · %H:%M") if value else ""


def _payload_items(payload, users_by_id: dict[int, User]) -> tuple[ActionPayloadItem, ...]:
    if isinstance(payload, AssignmentActionPayload):
        items: list[ActionPayloadItem] = []
        if payload.assigned_group is not None:
            items.append(ActionPayloadItem("Gruppo", payload.assigned_group.value))
        if payload.assigned_technician_id is not None:
            technician = users_by_id.get(payload.assigned_technician_id)
            items.append(
                ActionPayloadItem(
                    "Tecnico",
                    technician.display_name if technician else "Tecnico non disponibile",
                )
            )
        return tuple(items)
    if isinstance(payload, RequesterCommunicationPayload):
        return (ActionPayloadItem("Messaggio", payload.message),)
    if isinstance(payload, VendorEscalationPayload):
        return (
            ActionPayloadItem("Fornitore", payload.vendor_name),
            ActionPayloadItem("Riepilogo", payload.summary),
        )
    return ()


def present_action_proposals(
    session: Session,
    ticket_id: int,
) -> list[ProposedActionView]:
    proposals = list_action_proposals(session, ticket_id)
    user_ids = {
        identifier
        for proposal in proposals
        for identifier in (
            proposal.reviewed_by_user_id,
            (
                proposal.payload.assigned_technician_id
                if isinstance(proposal.payload, AssignmentActionPayload)
                else None
            ),
        )
        if identifier is not None
    }
    users = (
        session.scalars(select(User).where(User.id.in_(user_ids))).all()
        if user_ids
        else []
    )
    users_by_id = {user.id: user for user in users}

    return [
        ProposedActionView(
            id=proposal.id,
            type_label=ACTION_TYPE_LABELS[proposal.action_type],
            status_label=ACTION_STATUS_LABELS[proposal.status],
            status_class=ACTION_STATUS_CLASSES[proposal.status],
            rationale=proposal.rationale,
            expected_effect=proposal.expected_effect,
            payload_items=_payload_items(proposal.payload, users_by_id),
            can_decide=proposal.status is ActionStatus.PENDING_APPROVAL,
            reviewer_name=(
                users_by_id[proposal.reviewed_by_user_id].display_name
                if proposal.reviewed_by_user_id in users_by_id
                else ""
            ),
            decided_at=_format_datetime(proposal.decided_at),
            execution_reference=proposal.execution_reference or "",
            execution_message=proposal.execution_message or "",
        )
        for proposal in proposals
    ]
