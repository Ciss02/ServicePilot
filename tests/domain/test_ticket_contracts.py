"""Test dei contratti usati per creare e aggiornare i ticket."""

import pytest
from pydantic import ValidationError

from app.domain import Priority, TicketClassification, TicketCreate, TicketUpdate


def valid_ticket_create_data() -> dict[str, object]:
    return {
        "title": "Accesso VPN non disponibile",
        "description": "La connessione VPN mostra un errore prima dell'accesso.",
        "site_id": 3,
        "service": "Accesso remoto",
        "affected_users": 1,
        "confirmed": True,
    }


def test_ticket_create_accepts_confirmed_valid_data() -> None:
    data = valid_ticket_create_data()
    data["title"] = "  Accesso VPN non disponibile  "

    ticket = TicketCreate.model_validate(data)

    assert ticket.title == "Accesso VPN non disponibile"
    assert ticket.confirmed is True


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        pytest.param("title", "   ", id="blank-title"),
        pytest.param("description", "Breve", id="short-description"),
        pytest.param("site_id", 0, id="invalid-site"),
        pytest.param("affected_users", 0, id="no-affected-users"),
        pytest.param("confirmed", False, id="not-confirmed"),
        pytest.param("confirmed", 1, id="confirmation-is-not-boolean"),
    ],
)
def test_ticket_create_rejects_invalid_data(field: str, invalid_value: object) -> None:
    data = valid_ticket_create_data()
    data[field] = invalid_value

    with pytest.raises(ValidationError) as error:
        TicketCreate.model_validate(data)

    assert error.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize("field", ["priority", "requester_id"])
def test_ticket_create_rejects_unknown_fields(field: str) -> None:
    data = valid_ticket_create_data()
    data[field] = "p1" if field == "priority" else 12

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TicketCreate.model_validate(data)


def test_ticket_create_rejects_numeric_strings() -> None:
    data = valid_ticket_create_data()
    data["site_id"] = "3"

    with pytest.raises(ValidationError) as error:
        TicketCreate.model_validate(data)

    assert error.value.errors()[0]["loc"] == ("site_id",)


def test_classification_calculates_priority() -> None:
    classification = TicketClassification.model_validate(
        {
            "category": "network_and_connectivity",
            "subcategory": "VPN",
            "impact": "high",
            "urgency": "high",
        }
    )

    assert classification.priority is Priority.P1
    assert classification.model_dump(mode="json")["priority"] == "p1"


def test_classification_rejects_supplied_priority() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TicketClassification.model_validate(
            {
                "category": "network_and_connectivity",
                "impact": "high",
                "urgency": "high",
                "priority": "p4",
            }
        )


def test_classification_requires_impact_and_urgency_together() -> None:
    with pytest.raises(ValidationError) as error:
        TicketClassification.model_validate(
            {"category": "network_and_connectivity", "impact": "high"}
        )

    assert error.value.errors()[0]["loc"] == ("urgency",)


def test_classification_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError) as error:
        TicketClassification.model_validate(
            {"category": "unknown", "impact": "low", "urgency": "low"}
        )

    assert error.value.errors()[0]["loc"] == ("category",)


def test_ticket_update_accepts_partial_valid_data() -> None:
    update = TicketUpdate.model_validate(
        {"status": "in_progress", "technician_note": "Analisi avviata"}
    )

    assert update.status.value == "in_progress"
    assert update.technician_note == "Analisi avviata"


def test_ticket_update_accepts_complete_classification() -> None:
    update = TicketUpdate.model_validate(
        {
            "classification": {
                "category": "software_and_applications",
                "impact": "medium",
                "urgency": "high",
            }
        }
    )

    assert update.classification is not None
    assert update.classification.priority is Priority.P2


@pytest.mark.parametrize("data", [{}, {"title": None}], ids=["empty", "only-null"])
def test_ticket_update_rejects_empty_request(data: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="specificare almeno un campo"):
        TicketUpdate.model_validate(data)
