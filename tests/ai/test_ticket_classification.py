"""Verifiche della classificazione AI senza chiamate esterne."""

import json
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.ticket_classification import (
    AIProposedTicketClassification,
    classify_confirmed_ticket,
    suggest_ticket_classification,
)
from app.ai.contracts import AIInvalidResponseError, AIUnavailableError
from app.db import Site, Ticket, User, build_engine, create_database
from app.domain.vocabulary import (
    AssignmentGroup,
    ClassificationReviewStatus,
    Priority,
    Role,
)


class ClassificationModelStub:
    """Restituisce una proposta controllata e registra la richiesta ricevuta."""

    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[AIProposedTicketClassification],
        system_instruction: str | None = None,
    ) -> AIProposedTicketClassification:
        self.calls.append(
            {
                "prompt": prompt,
                "response_schema": response_schema,
                "system_instruction": system_instruction,
            }
        )
        if isinstance(self.response, dict):
            return response_schema.model_validate(self.response)
        return self.response  # type: ignore[return-value]


class FailingClassificationModelStub:
    """Simula un errore controllato senza collegamenti esterni."""

    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    def generate_structured(self, **_kwargs):
        self.calls += 1
        raise self.error


def valid_proposal() -> dict[str, object]:
    return {
        "category": "network_and_connectivity",
        "subcategory": "VPN",
        "impact": "high",
        "urgency": "medium",
        "assigned_group": "Supporto rete",
    }


def ticket_and_site() -> tuple[Ticket, Site]:
    ticket = Ticket(
        id=12,
        title="VPN non disponibile nella sede demo",
        description="La VPN è bloccata per tutte le persone della sede demo.",
        requester_id=4,
        site_id=3,
        service="Accesso remoto",
        affected_users=18,
    )
    site = Site(id=3, code="HQ-DEMO", name="Sede centrale demo")
    return ticket, site


def test_suggestion_uses_controlled_options_and_backend_priority() -> None:
    ticket, site = ticket_and_site()
    model = ClassificationModelStub(valid_proposal())

    suggestion = suggest_ticket_classification(
        ticket,
        site=site,
        ai_model=model,
    )

    assert suggestion.category.value == "network_and_connectivity"
    assert suggestion.subcategory == "VPN"
    assert suggestion.assigned_group is AssignmentGroup.NETWORK_SUPPORT
    assert suggestion.priority is Priority.P2
    call = model.calls[0]
    assert call["response_schema"] is AIProposedTicketClassification
    prompt = json.loads(call["prompt"])
    assert prompt["ticket"]["site"] == {
        "code": "HQ-DEMO",
        "name": "Sede centrale demo",
    }
    assert "p1" not in prompt
    assert "Supporto rete" in prompt["allowed_assignment_groups"]
    assert "non proporre né restituire la priorità" in call[
        "system_instruction"
    ].casefold()


@pytest.mark.parametrize(
    "invalid_change",
    [
        {"category": "invented_category"},
        {"impact": "critical"},
        {"urgency": "immediate"},
        {"assigned_group": "Gruppo inventato"},
        {"priority": "p1"},
    ],
)
def test_response_contract_rejects_unknown_values_and_model_priority(
    invalid_change: dict[str, object],
) -> None:
    payload = {**valid_proposal(), **invalid_change}

    with pytest.raises(ValidationError):
        AIProposedTicketClassification.model_validate(payload)


def test_classification_is_saved_once_with_deterministic_priority(tmp_path) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / 'classification.db'}")
    create_database(engine)
    model = ClassificationModelStub(valid_proposal())
    with Session(engine) as session:
        site = Site(code="HQ-DEMO", name="Sede centrale demo")
        requester = User(
            email="dipendente.classificazione@servicepilot.example",
            display_name="Dipendente Classificazione Demo",
            role=Role.EMPLOYEE,
        )
        session.add_all([site, requester])
        session.flush()
        ticket = Ticket(
            title="VPN non disponibile nella sede demo",
            description="La VPN è bloccata per tutte le persone della sede demo.",
            requester_id=requester.id,
            site_id=site.id,
            service="Accesso remoto",
            affected_users=18,
        )
        session.add(ticket)
        session.commit()

        classified = classify_confirmed_ticket(session, ticket, ai_model=model)
        classified_again = classify_confirmed_ticket(session, ticket, ai_model=model)

        assert classified_again is classified
        assert classified.category.value == "network_and_connectivity"
        assert classified.subcategory == "VPN"
        assert classified.impact.value == "high"
        assert classified.urgency.value == "medium"
        assert classified.priority is Priority.P2
        assert classified.assigned_group == "Supporto rete"
        assert (
            classified.classification_review_status
            is ClassificationReviewStatus.AI_SUGGESTED
        )
        assert len(model.calls) == 1
    engine.dispose()


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (
            AIUnavailableError("timeout simulato"),
            ClassificationReviewStatus.AI_UNAVAILABLE,
        ),
        (
            AIInvalidResponseError("risposta simulata non valida"),
            ClassificationReviewStatus.AI_INVALID_RESPONSE,
        ),
    ],
)
def test_ai_failure_is_recorded_without_losing_or_retrying_the_ticket(
    tmp_path,
    error: Exception,
    expected_status: ClassificationReviewStatus,
) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / f'{expected_status.value}.db'}")
    create_database(engine)
    model = FailingClassificationModelStub(error)
    with Session(engine) as session:
        site = Site(code="FAIL-DEMO", name="Sede errore AI demo")
        requester = User(
            email=f"{expected_status.value}@servicepilot.example",
            display_name="Dipendente Errore AI Demo",
            role=Role.EMPLOYEE,
        )
        session.add_all([site, requester])
        session.flush()
        ticket = Ticket(
            title="Richiesta demo da classificare",
            description="Questa richiesta fittizia verifica un errore controllato.",
            requester_id=requester.id,
            site_id=site.id,
            service="Servizio demo",
            affected_users=1,
        )
        session.add(ticket)
        session.commit()

        classified = classify_confirmed_ticket(session, ticket, ai_model=model)
        classified_again = classify_confirmed_ticket(session, ticket, ai_model=model)

        assert classified_again is classified
        assert classified.classification_review_status is expected_status
        assert classified.category is None
        assert classified.priority is None
        assert model.calls == 1
    engine.dispose()
