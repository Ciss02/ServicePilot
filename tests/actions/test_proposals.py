"""Verifica che una proposta salvata non venga mai applicata al ticket."""

import json

import pytest
from sqlalchemy.orm import Session

from app.actions import (
    ActionProposalDataError,
    ActionProposalPersistenceError,
    create_action_proposal,
    list_action_proposals,
)
from app.db import ProposedAction, Site, Ticket, User, build_engine, create_database
from app.domain import (
    ActionProposalCreate,
    ActionStatus,
    ActionType,
    AssignmentActionPayload,
    RequesterCommunicationPayload,
    VendorEscalationPayload,
)
from app.domain.vocabulary import AssignmentGroup, Role, TicketStatus


@pytest.fixture
def action_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'actions-test.db'}")
    create_database(engine)
    with Session(engine) as session:
        requester = User(
            email="richiedente.azioni@example.test",
            display_name="Richiedente Azioni Demo",
            role=Role.EMPLOYEE,
        )
        site = Site(code="ACT-DEMO", name="Sede Azioni Demo")
        session.add_all([requester, site])
        session.flush()
        ticket = Ticket(
            title="VPN demo da verificare",
            description="La connessione remota demo si interrompe durante il lavoro.",
            requester_id=requester.id,
            site_id=site.id,
            service="Accesso remoto",
            affected_users=1,
        )
        session.add(ticket)
        session.commit()
        ticket_id = ticket.id
    yield engine, ticket_id
    engine.dispose()


def _proposal(action_type: ActionType) -> ActionProposalCreate:
    payloads = {
        ActionType.ASSIGN_TICKET: AssignmentActionPayload(
            assigned_group=AssignmentGroup.NETWORK_SUPPORT
        ),
        ActionType.NOTIFY_REQUESTER: RequesterCommunicationPayload(
            message="Indica l'orario dell'ultima interruzione della VPN demo."
        ),
        ActionType.ESCALATE_VENDOR: VendorEscalationPayload(
            vendor_name="Rete Partner Demo",
            summary="Verificare la linea fittizia della sede Azioni Demo.",
        ),
    }
    return ActionProposalCreate(
        action_type=action_type,
        rationale="La verifica corrente suggerisce questo prossimo passo controllato.",
        payload=payloads[action_type],
        expected_effect="L'azione sarà disponibile per la revisione del tecnico.",
    )


@pytest.mark.parametrize("action_type", list(ActionType))
def test_saving_proposal_never_applies_it_to_ticket(
    action_context,
    action_type: ActionType,
) -> None:
    engine, ticket_id = action_context
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)

        action = create_action_proposal(session, ticket, _proposal(action_type))

        session.refresh(ticket)
        assert action.status is ActionStatus.PENDING_APPROVAL
        assert ticket.status is TicketStatus.NEW
        assert ticket.assigned_group is None
        assert ticket.assigned_technician_id is None
        assert ticket.technician_note is None
        assert ticket.resolution is None


def test_proposal_is_saved_with_valid_json_and_can_be_read(action_context) -> None:
    engine, ticket_id = action_context
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        stored = create_action_proposal(
            session,
            ticket,
            _proposal(ActionType.ASSIGN_TICKET),
        )

        assert json.loads(stored.payload_json) == {
            "assigned_group": "Supporto rete",
            "assigned_technician_id": None,
        }
        proposals = list_action_proposals(session, ticket_id)
        assert len(proposals) == 1
        assert proposals[0].id == stored.id
        assert proposals[0].ticket_id == ticket_id
        assert proposals[0].status is ActionStatus.PENDING_APPROVAL
        assert isinstance(proposals[0].payload, AssignmentActionPayload)


def test_newest_proposal_is_listed_first(action_context) -> None:
    engine, ticket_id = action_context
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        first = create_action_proposal(
            session,
            ticket,
            _proposal(ActionType.NOTIFY_REQUESTER),
        )
        second = create_action_proposal(
            session,
            ticket,
            _proposal(ActionType.ESCALATE_VENDOR),
        )

        proposals = list_action_proposals(session, ticket_id)
        assert [proposal.id for proposal in proposals] == [second.id, first.id]


def test_unknown_ticket_prevents_proposal_persistence(action_context) -> None:
    engine, _ = action_context
    with Session(engine) as session:
        missing_ticket = Ticket(id=999)

        with pytest.raises(ActionProposalPersistenceError):
            create_action_proposal(
                session,
                missing_ticket,
                _proposal(ActionType.NOTIFY_REQUESTER),
            )


def test_corrupted_stored_payload_is_reported(action_context) -> None:
    engine, ticket_id = action_context
    with Session(engine) as session:
        session.add(
            ProposedAction(
                ticket_id=ticket_id,
                action_type=ActionType.NOTIFY_REQUESTER,
                rationale="La proposta fittizia contiene dati corrotti da rilevare.",
                payload_json="not-json",
                expected_effect="Il sistema deve rifiutare una lettura non affidabile.",
            )
        )
        session.commit()

        with pytest.raises(ActionProposalDataError):
            list_action_proposals(session, ticket_id)
