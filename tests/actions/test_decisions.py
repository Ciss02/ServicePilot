"""Verifica approvazione umana, rifiuto e singola esecuzione delle proposte."""

import json
from collections.abc import Callable

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.actions import (
    ActionAlreadyDecidedError,
    ActionDecisionForbiddenError,
    ActionExecutionResult,
    ActionNotFoundError,
    ActionServiceError,
    create_action_proposal,
    decide_action_proposal,
)
from app.db import (
    AuditEvent,
    ProposedAction,
    Site,
    Ticket,
    User,
    build_engine,
    create_database,
)
from app.domain import (
    ActionDecision,
    ActionProposalCreate,
    ActionStatus,
    ActionType,
    RequesterCommunicationPayload,
)
from app.domain.vocabulary import Role, TicketStatus
from app.domain.vocabulary import AuditEventType


class ActionServiceStub:
    def __init__(
        self,
        result: ActionExecutionResult | None = None,
        before_result: Callable[[], None] | None = None,
        error: ActionServiceError | None = None,
    ) -> None:
        self.result = result or ActionExecutionResult(
            succeeded=True,
            reference="COM-DEMO-071",
            message="Comunicazione demo registrata senza inviare messaggi reali.",
        )
        self.before_result = before_result
        self.error = error
        self.calls = []

    def execute(self, proposal):
        self.calls.append(proposal)
        if self.before_result:
            self.before_result()
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def decision_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'action-decisions.db'}")
    create_database(engine)
    with Session(engine) as session:
        employee = User(
            email="dipendente.decisioni@example.test",
            display_name="Dipendente Decisioni Demo",
            role=Role.EMPLOYEE,
        )
        technician = User(
            email="tecnico.decisioni@example.test",
            display_name="Tecnico Decisioni Demo",
            role=Role.TECHNICIAN,
        )
        admin = User(
            email="admin.decisioni@example.test",
            display_name="Admin Decisioni Demo",
            role=Role.ADMIN,
        )
        site = Site(code="DEC-DEMO", name="Sede Decisioni Demo")
        session.add_all([employee, technician, admin, site])
        session.flush()
        ticket = Ticket(
            title="Comunicazione demo da approvare",
            description="Il richiedente attende un aggiornamento completamente fittizio.",
            requester_id=employee.id,
            site_id=site.id,
            service="Comunicazioni demo",
            affected_users=1,
        )
        other_ticket = Ticket(
            title="Secondo ticket demo",
            description="Ticket distinto usato per controllare i riferimenti.",
            requester_id=employee.id,
            site_id=site.id,
            service="Servizio demo",
            affected_users=1,
        )
        session.add_all([ticket, other_ticket])
        session.commit()
        action = create_action_proposal(
            session,
            ticket,
            ActionProposalCreate(
                action_type=ActionType.NOTIFY_REQUESTER,
                rationale=(
                    "Il richiedente deve ricevere un aggiornamento fittizio controllato."
                ),
                payload=RequesterCommunicationPayload(
                    message="La verifica demo è in corso e seguirà un aggiornamento."
                ),
                expected_effect=(
                    "Registrare una comunicazione demo senza inviare messaggi reali."
                ),
            ),
        )
        context = {
            "engine": engine,
            "ticket_id": ticket.id,
            "other_ticket_id": other_ticket.id,
            "action_id": action.id,
            "employee_id": employee.id,
            "technician_id": technician.id,
            "admin_id": admin.id,
        }
    yield context
    engine.dispose()


def _user(session: Session, context: dict, key: str) -> User:
    return session.get(User, context[key])


def test_rejection_is_saved_without_calling_the_service(decision_context) -> None:
    client = ActionServiceStub()
    with Session(decision_context["engine"]) as session:
        result = decide_action_proposal(
            session,
            ticket_id=decision_context["ticket_id"],
            action_id=decision_context["action_id"],
            reviewer=_user(session, decision_context, "technician_id"),
            decision=ActionDecision.REJECT,
            service_client=client,
        )

        assert result.status is ActionStatus.REJECTED
        assert result.reviewed_by_user_id == decision_context["technician_id"]
        assert result.decided_at is not None
        assert result.execution_reference is None
        assert client.calls == []
        event_types = list(
            session.scalars(
                select(AuditEvent.event_type).where(
                    AuditEvent.ticket_id == decision_context["ticket_id"]
                )
            ).all()
        )
        assert event_types == [
            AuditEventType.ACTION_PROPOSED,
            AuditEventType.ACTION_REJECTED,
        ]


def test_approval_is_persisted_before_exactly_one_service_call(
    decision_context,
) -> None:
    def assert_execution_was_claimed() -> None:
        with Session(decision_context["engine"]) as verification_session:
            stored = verification_session.get(
                ProposedAction,
                decision_context["action_id"],
            )
            assert stored.status is ActionStatus.EXECUTING
            assert stored.reviewed_by_user_id == decision_context["technician_id"]
            assert stored.decided_at is not None

    client = ActionServiceStub(before_result=assert_execution_was_claimed)
    with Session(decision_context["engine"]) as session:
        result = decide_action_proposal(
            session,
            ticket_id=decision_context["ticket_id"],
            action_id=decision_context["action_id"],
            reviewer=_user(session, decision_context, "technician_id"),
            decision=ActionDecision.APPROVE,
            service_client=client,
        )

        assert result.status is ActionStatus.SUCCEEDED
        assert result.execution_reference == "COM-DEMO-071"
        assert len(client.calls) == 1
        ticket = session.get(Ticket, decision_context["ticket_id"])
        assert ticket.status is TicketStatus.NEW
        assert ticket.technician_note is None
        events = list(
            session.scalars(
                select(AuditEvent)
                .where(AuditEvent.ticket_id == decision_context["ticket_id"])
                .order_by(AuditEvent.id)
            ).all()
        )
        assert [event.event_type for event in events] == [
            AuditEventType.ACTION_PROPOSED,
            AuditEventType.ACTION_APPROVED,
            AuditEventType.ACTION_EXECUTION_STARTED,
            AuditEventType.ACTION_EXECUTION_SUCCEEDED,
        ]
        assert json.loads(events[-1].details_json)["reference"] == "COM-DEMO-071"


def test_controlled_service_failure_is_visible_and_persisted(decision_context) -> None:
    client = ActionServiceStub(
        result=ActionExecutionResult(
            succeeded=False,
            message="Errore demo ripetibile del servizio simulato.",
            error_code="simulated_service_unavailable",
        )
    )
    with Session(decision_context["engine"]) as session:
        result = decide_action_proposal(
            session,
            ticket_id=decision_context["ticket_id"],
            action_id=decision_context["action_id"],
            reviewer=_user(session, decision_context, "admin_id"),
            decision=ActionDecision.APPROVE,
            service_client=client,
        )

        assert result.status is ActionStatus.FAILED
        assert result.execution_error_code == "simulated_service_unavailable"
        assert "Errore demo" in result.execution_message
        assert len(client.calls) == 1


def test_unreachable_service_does_not_turn_into_a_false_success(
    decision_context,
) -> None:
    client = ActionServiceStub(error=ActionServiceError("connessione demo assente"))
    with Session(decision_context["engine"]) as session:
        result = decide_action_proposal(
            session,
            ticket_id=decision_context["ticket_id"],
            action_id=decision_context["action_id"],
            reviewer=_user(session, decision_context, "technician_id"),
            decision=ActionDecision.APPROVE,
            service_client=client,
        )

        assert result.status is ActionStatus.FAILED
        assert result.execution_error_code == "simulated_service_unreachable"
        assert "non è raggiungibile" in result.execution_message


def test_employee_cannot_decide_or_call_the_service(decision_context) -> None:
    client = ActionServiceStub()
    with Session(decision_context["engine"]) as session:
        with pytest.raises(ActionDecisionForbiddenError):
            decide_action_proposal(
                session,
                ticket_id=decision_context["ticket_id"],
                action_id=decision_context["action_id"],
                reviewer=_user(session, decision_context, "employee_id"),
                decision=ActionDecision.APPROVE,
                service_client=client,
            )

        assert client.calls == []
        assert (
            session.get(ProposedAction, decision_context["action_id"]).status
            is ActionStatus.PENDING_APPROVAL
        )


def test_action_from_another_ticket_is_hidden_and_never_called(
    decision_context,
) -> None:
    client = ActionServiceStub()
    with Session(decision_context["engine"]) as session:
        with pytest.raises(ActionNotFoundError):
            decide_action_proposal(
                session,
                ticket_id=decision_context["other_ticket_id"],
                action_id=decision_context["action_id"],
                reviewer=_user(session, decision_context, "technician_id"),
                decision=ActionDecision.APPROVE,
                service_client=client,
            )
        assert client.calls == []


def test_second_decision_never_repeats_the_service_call(decision_context) -> None:
    client = ActionServiceStub()
    with Session(decision_context["engine"]) as session:
        reviewer = _user(session, decision_context, "technician_id")
        decide_action_proposal(
            session,
            ticket_id=decision_context["ticket_id"],
            action_id=decision_context["action_id"],
            reviewer=reviewer,
            decision=ActionDecision.APPROVE,
            service_client=client,
        )
        with pytest.raises(ActionAlreadyDecidedError):
            decide_action_proposal(
                session,
                ticket_id=decision_context["ticket_id"],
                action_id=decision_context["action_id"],
                reviewer=reviewer,
                decision=ActionDecision.APPROVE,
                service_client=client,
            )

        assert len(client.calls) == 1
