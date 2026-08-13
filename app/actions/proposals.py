"""Persistenza delle proposte, volutamente separata da qualsiasi esecuzione."""

import json

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.audit import record_action_proposed
from app.db.models import ProposedAction, SupportGroup, Ticket
from app.domain.action_contracts import (
    ActionProposalCreate,
    ActionProposalRead,
    AssignmentActionPayload,
)
from app.domain.vocabulary import ActionStatus, ActionType


class ActionProposalPersistenceError(RuntimeError):
    """La proposta non può essere salvata in modo completo."""


class ActionProposalDataError(RuntimeError):
    """Una proposta salvata contiene dati non più validi o leggibili."""


class ActionProposalDestinationError(RuntimeError):
    """La destinazione proposta non è disponibile nel catalogo operativo."""


def read_action_proposal(row: ProposedAction) -> ActionProposalRead:
    """Converte una riga persistente nel contratto specifico e controllato."""

    try:
        return ActionProposalRead.model_validate(
            {
                "id": row.id,
                "ticket_id": row.ticket_id,
                "action_type": row.action_type,
                "rationale": row.rationale,
                "payload": json.loads(row.payload_json),
                "expected_effect": row.expected_effect,
                "status": row.status,
                "reviewed_by_user_id": row.reviewed_by_user_id,
                "decided_at": row.decided_at,
                "execution_reference": row.execution_reference,
                "execution_message": row.execution_message,
                "execution_error_code": row.execution_error_code,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        )
    except (json.JSONDecodeError, TypeError, ValidationError) as error:
        raise ActionProposalDataError from error


def create_action_proposal(
    session: Session,
    ticket: Ticket,
    proposal: ActionProposalCreate,
) -> ProposedAction:
    """Salva soltanto l'intenzione dell'agente, senza applicarla al ticket."""

    if (
        proposal.action_type is ActionType.ASSIGN_TICKET
        and isinstance(proposal.payload, AssignmentActionPayload)
        and proposal.payload.assigned_group is not None
        and session.scalar(
            select(SupportGroup.id).where(
                SupportGroup.name == proposal.payload.assigned_group,
                SupportGroup.is_active.is_(True),
            )
        )
        is None
    ):
        raise ActionProposalDestinationError

    action = ProposedAction(
        ticket_id=ticket.id,
        action_type=proposal.action_type,
        rationale=proposal.rationale,
        payload_json=json.dumps(
            proposal.payload.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
        ),
        expected_effect=proposal.expected_effect,
        status=ActionStatus.PENDING_APPROVAL,
    )
    session.add(action)
    try:
        session.flush()
        record_action_proposed(session, action)
        session.commit()
        session.refresh(action)
    except SQLAlchemyError as error:
        session.rollback()
        raise ActionProposalPersistenceError from error
    return action


def list_action_proposals(
    session: Session,
    ticket_id: int,
) -> list[ActionProposalRead]:
    """Ricarica le proposte del ticket dalla più recente alla più vecchia."""

    rows = session.scalars(
        select(ProposedAction)
        .where(ProposedAction.ticket_id == ticket_id)
        .order_by(ProposedAction.created_at.desc(), ProposedAction.id.desc())
    ).all()
    return [read_action_proposal(row) for row in rows]
