"""Verifiche dei dati ammessi per ogni tipo di proposta."""

import pytest
from pydantic import ValidationError

from app.domain import (
    ActionProposalCreate,
    ActionType,
    AssignmentActionPayload,
    RequesterCommunicationPayload,
    VendorEscalationPayload,
)
from app.domain.vocabulary import AssignmentGroup


def test_assignment_proposal_accepts_controlled_group_or_technician() -> None:
    proposal = ActionProposalCreate(
        action_type=ActionType.ASSIGN_TICKET,
        rationale="Il problema riguarda la connettività della sede demo.",
        payload=AssignmentActionPayload(
            assigned_group=AssignmentGroup.NETWORK_SUPPORT,
            assigned_technician_id=3,
        ),
        expected_effect="Il ticket sarà preso in carico dal supporto rete.",
    )

    assert proposal.payload.assigned_group is AssignmentGroup.NETWORK_SUPPORT
    assert proposal.payload.assigned_technician_id == 3


def test_requester_communication_and_vendor_escalation_have_distinct_data() -> None:
    communication = ActionProposalCreate(
        action_type=ActionType.NOTIFY_REQUESTER,
        rationale="Serve chiedere un orario preciso per riprodurre il problema.",
        payload=RequesterCommunicationPayload(
            message="Indica l'orario dell'ultima interruzione della VPN demo."
        ),
        expected_effect="Il richiedente fornirà il dettaglio mancante nel ticket.",
    )
    escalation = ActionProposalCreate(
        action_type=ActionType.ESCALATE_VENDOR,
        rationale="La procedura interna richiede una verifica esterna simulata.",
        payload=VendorEscalationPayload(
            vendor_name="Rete Partner Demo",
            summary="Verificare la linea fittizia del punto vendita Nova Demo.",
        ),
        expected_effect="Il fornitore demo riceverà una richiesta di verifica.",
    )

    assert isinstance(communication.payload, RequesterCommunicationPayload)
    assert isinstance(escalation.payload, VendorEscalationPayload)


def test_assignment_requires_a_destination() -> None:
    with pytest.raises(ValidationError, match="gruppo o un tecnico"):
        AssignmentActionPayload()


def test_action_type_must_match_its_payload() -> None:
    with pytest.raises(ValidationError, match="non corrispondono"):
        ActionProposalCreate(
            action_type=ActionType.ASSIGN_TICKET,
            rationale="Il tecnico deve ricevere informazioni aggiuntive controllate.",
            payload=RequesterCommunicationPayload(
                message="Invia al richiedente una domanda dimostrativa."
            ),
            expected_effect="Il richiedente vedrà la comunicazione proposta.",
        )


def test_creation_contract_does_not_accept_status_from_outside() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ActionProposalCreate(
            action_type=ActionType.NOTIFY_REQUESTER,
            rationale="Lo stato iniziale deve essere deciso soltanto dal backend.",
            payload=RequesterCommunicationPayload(
                message="Conferma la disponibilità per una prova dimostrativa."
            ),
            expected_effect="La proposta resterà in attesa della revisione tecnica.",
            status="succeeded",
        )


@pytest.mark.parametrize(
    "field_values",
    [
        {"rationale": "Troppo breve"},
        {"expected_effect": "Breve"},
        {"action_type": "delete_ticket"},
    ],
)
def test_proposal_rejects_incomplete_or_unknown_values(field_values) -> None:
    values = {
        "action_type": ActionType.NOTIFY_REQUESTER,
        "rationale": "Manca un dettaglio necessario per proseguire in sicurezza.",
        "payload": RequesterCommunicationPayload(
            message="Puoi indicare quando è iniziato il problema demo?"
        ),
        "expected_effect": "Il ticket riceverà l'informazione richiesta.",
    }
    values.update(field_values)

    with pytest.raises(ValidationError):
        ActionProposalCreate(**values)
