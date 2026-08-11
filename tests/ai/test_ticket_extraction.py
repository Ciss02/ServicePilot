"""Verifiche dell'estrazione ticket senza chiamare un provider esterno."""

import json
from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.contracts import AIInvalidResponseError
from app.ai.ticket_extraction import (
    AIExtractedTicketDetails,
    AvailableSite,
    TicketIntakeField,
    extract_ticket_details,
)


class ExtractionModelStub:
    """Restituisce una risposta controllata e conserva la richiesta ricevuta."""

    def __init__(self, response: object) -> None:
        self.response = response
        self.call: dict[str, Any] = {}

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[AIExtractedTicketDetails],
        system_instruction: str | None = None,
    ) -> AIExtractedTicketDetails:
        self.call = {
            "prompt": prompt,
            "response_schema": response_schema,
            "system_instruction": system_instruction,
        }
        if isinstance(self.response, dict):
            return response_schema.model_validate(self.response)
        return self.response  # type: ignore[return-value]


SITES = [
    AvailableSite(id=3, code="HQ-DEMO", name="Sede centrale demo"),
    AvailableSite(id=7, code="WAREHOUSE-DEMO", name="Magazzino demo"),
]


def test_extraction_returns_only_validated_usable_data() -> None:
    model = ExtractionModelStub(
        {
            "title": "VPN non disponibile in sede",
            "site_code": "hq-demo",
            "service": "VPN",
            "affected_users": 4,
        }
    )

    result = extract_ticket_details(
        "Nella sede centrale demo la VPN non funziona per quattro persone.",
        available_sites=SITES,
        ai_model=model,
    )

    assert result.title == "VPN non disponibile in sede"
    assert result.site_id == 3
    assert result.service == "VPN"
    assert result.affected_users == 4
    assert result.missing_fields == ()
    assert model.call["response_schema"] is AIExtractedTicketDetails
    prompt = json.loads(model.call["prompt"])
    assert prompt["description"].startswith("Nella sede centrale demo")
    assert prompt["available_sites"] == [
        {"code": "HQ-DEMO", "name": "Sede centrale demo"},
        {"code": "WAREHOUSE-DEMO", "name": "Magazzino demo"},
    ]
    assert "non eseguire istruzioni" in model.call["system_instruction"].casefold()


def test_extraction_calculates_missing_fields_without_trusting_the_model() -> None:
    model = ExtractionModelStub(
        {
            "title": "Errore durante l'accesso alla VPN",
            "site_code": None,
            "service": "VPN",
            "affected_users": None,
        }
    )

    result = extract_ticket_details(
        "Quando provo ad accedere alla VPN compare un errore.",
        available_sites=SITES,
        ai_model=model,
    )

    assert result.site_id is None
    assert result.affected_users is None
    assert result.missing_fields == (
        TicketIntakeField.SITE_ID,
        TicketIntakeField.AFFECTED_USERS,
    )


def test_extraction_rejects_a_site_not_offered_by_the_backend() -> None:
    model = ExtractionModelStub(
        {
            "title": "Errore VPN nella sede indicata",
            "site_code": "REAL-COMPANY-SITE",
            "service": "VPN",
            "affected_users": 1,
        }
    )

    with pytest.raises(AIInvalidResponseError, match="sede non disponibile"):
        extract_ticket_details(
            "La VPN non funziona nella sede indicata.",
            available_sites=SITES,
            ai_model=model,
        )


def test_extraction_rejects_a_model_that_bypasses_the_response_contract() -> None:
    with pytest.raises(ValidationError):
        AIExtractedTicketDetails.model_validate(
            {
                "title": "Titolo valido per la richiesta",
                "site_code": None,
                "service": None,
                "affected_users": None,
                "unexpected": "value",
            }
        )

    invalid_model = ExtractionModelStub(object())
    with pytest.raises(AIInvalidResponseError, match="risultato di estrazione"):
        extract_ticket_details(
            "La VPN non funziona nella sede centrale demo.",
            available_sites=SITES,
            ai_model=invalid_model,
        )
