"""Decisione umana ed esecuzione controllata delle azioni proposte."""

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.actions.proposals import read_action_proposal
from app.actions.service_client import (
    ActionExecutionResult,
    ActionServiceClient,
    ActionServiceError,
)
from app.audit import (
    record_action_decision,
    record_action_execution_result,
    record_action_execution_started,
)
from app.db.models import ProposedAction, User
from app.domain.vocabulary import ActionDecision, ActionStatus, Role


class ActionDecisionError(RuntimeError):
    """Errore controllato durante una decisione sull'azione."""


class ActionNotFoundError(ActionDecisionError):
    """La proposta non appartiene al ticket indicato."""


class ActionAlreadyDecidedError(ActionDecisionError):
    """La proposta non è più in attesa e non deve essere ripetuta."""


class ActionDecisionForbiddenError(ActionDecisionError):
    """Il profilo non può decidere azioni operative."""


class ActionDecisionPersistenceError(ActionDecisionError):
    """La decisione o il suo risultato non possono essere salvati."""


def _commit_update(
    session: Session,
    statement,
    *,
    record_event: Callable[[], object] | None = None,
) -> bool:
    try:
        result = session.execute(statement)
        if result.rowcount == 1 and record_event is not None:
            record_event()
        session.commit()
        return result.rowcount == 1
    except SQLAlchemyError as error:
        session.rollback()
        raise ActionDecisionPersistenceError from error


def _service_failure(error: ActionServiceError) -> ActionExecutionResult:
    del error
    return ActionExecutionResult(
        succeeded=False,
        error_code="simulated_service_unreachable",
        message=(
            "Il servizio simulato non è raggiungibile. "
            "L'approvazione è salvata, ma l'azione non è riuscita."
        ),
    )


def decide_action_proposal(
    session: Session,
    *,
    ticket_id: int,
    action_id: int,
    reviewer: User,
    decision: ActionDecision,
    service_client: ActionServiceClient,
) -> ProposedAction:
    """Salva la decisione e chiama il servizio soltanto dopo l'approvazione."""

    if reviewer.role not in {Role.TECHNICIAN, Role.ADMIN}:
        raise ActionDecisionForbiddenError

    action = session.get(ProposedAction, action_id)
    if action is None or action.ticket_id != ticket_id:
        raise ActionNotFoundError
    if action.status is not ActionStatus.PENDING_APPROVAL:
        raise ActionAlreadyDecidedError

    proposal = read_action_proposal(action)
    decided_at = datetime.now(UTC)
    target_status = (
        ActionStatus.APPROVED if decision is ActionDecision.APPROVE else ActionStatus.REJECTED
    )
    claimed = _commit_update(
        session,
        update(ProposedAction)
        .where(
            ProposedAction.id == action_id,
            ProposedAction.ticket_id == ticket_id,
            ProposedAction.status == ActionStatus.PENDING_APPROVAL,
        )
        .values(
            status=target_status,
            reviewed_by_user_id=reviewer.id,
            decided_at=decided_at,
            execution_reference=None,
            execution_message=None,
            execution_error_code=None,
        ),
        record_event=lambda: record_action_decision(
            session,
            action,
            reviewer=reviewer,
            decision=decision,
        ),
    )
    if not claimed:
        raise ActionAlreadyDecidedError

    if decision is ActionDecision.REJECT:
        session.expire_all()
        return session.get(ProposedAction, action_id)

    started = _commit_update(
        session,
        update(ProposedAction)
        .where(
            ProposedAction.id == action_id,
            ProposedAction.status == ActionStatus.APPROVED,
        )
        .values(status=ActionStatus.EXECUTING),
        record_event=lambda: record_action_execution_started(session, action),
    )
    if not started:
        raise ActionAlreadyDecidedError

    try:
        execution = service_client.execute(proposal)
    except ActionServiceError as error:
        execution = _service_failure(error)

    final_status = ActionStatus.SUCCEEDED if execution.succeeded else ActionStatus.FAILED
    saved = _commit_update(
        session,
        update(ProposedAction)
        .where(
            ProposedAction.id == action_id,
            ProposedAction.status == ActionStatus.EXECUTING,
        )
        .values(
            status=final_status,
            execution_reference=execution.reference,
            execution_message=execution.message,
            execution_error_code=execution.error_code,
        ),
        record_event=lambda: record_action_execution_result(session, action),
    )
    if not saved:
        raise ActionDecisionPersistenceError

    session.expire_all()
    return session.get(ProposedAction, action_id)
