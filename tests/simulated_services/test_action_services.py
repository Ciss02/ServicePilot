"""Verifica successi, errori e separazione dei servizi REST simulati."""

from copy import deepcopy
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app as portal_app
from app.simulated_services.main import app as simulated_services_app


REQUEST_ID = "d96fb76d-9bd1-49dc-a397-88f7dc07df42"

SUCCESS_CASES = (
    (
        "/assignments",
        "assign_ticket",
        "ASG-D96FB76D9BD1",
        {
            "assigned_group": "Supporto rete",
            "assigned_technician_id": None,
        },
    ),
    (
        "/requester-communications",
        "notify_requester",
        "COM-D96FB76D9BD1",
        {"message": "Indica l'orario dell'ultima interruzione della VPN demo."},
    ),
    (
        "/vendor-escalations",
        "escalate_vendor",
        "ESC-D96FB76D9BD1",
        {
            "vendor_name": "Rete Partner Demo",
            "summary": "Verificare la linea fittizia della sede Azioni Demo.",
        },
    ),
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(simulated_services_app)


def _request(payload: dict, scenario: str = "success") -> dict:
    return {
        "request_id": REQUEST_ID,
        "ticket_id": 7,
        "simulation_scenario": scenario,
        "payload": payload,
    }


def test_simulated_services_health_is_independent(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "simulated-action-services",
    }


@pytest.mark.parametrize("path,action_type,reference,payload", SUCCESS_CASES)
def test_each_action_returns_a_reproducible_success(
    client: TestClient,
    path: str,
    action_type: str,
    reference: str,
    payload: dict,
) -> None:
    first = client.post(path, json=_request(payload))
    second = client.post(path, json=_request(payload))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json() == {
        "request_id": REQUEST_ID,
        "ticket_id": 7,
        "action_type": action_type,
        "result": "succeeded",
        "reference": reference,
        "message": first.json()["message"],
    }


@pytest.mark.parametrize("path,action_type,_reference,payload", SUCCESS_CASES)
def test_each_action_can_return_the_same_controlled_failure(
    client: TestClient,
    path: str,
    action_type: str,
    _reference: str,
    payload: dict,
) -> None:
    first = client.post(path, json=_request(payload, "service_unavailable"))
    second = client.post(path, json=_request(payload, "service_unavailable"))

    assert first.status_code == 503
    assert first.json() == second.json()
    assert first.json() == {
        "request_id": REQUEST_ID,
        "ticket_id": 7,
        "action_type": action_type,
        "result": "failed",
        "error_code": "simulated_service_unavailable",
        "message": (
            "Errore demo: il servizio simulato non è temporaneamente disponibile."
        ),
        "retryable": True,
    }


@pytest.mark.parametrize("path,_action_type,_reference,payload", SUCCESS_CASES)
def test_request_contracts_reject_invalid_or_unexpected_data(
    client: TestClient,
    path: str,
    _action_type: str,
    _reference: str,
    payload: dict,
) -> None:
    invalid = _request(deepcopy(payload))
    invalid["ticket_id"] = 0
    invalid["unexpected_command"] = "execute_for_real"

    response = client.post(path, json=invalid)

    assert response.status_code == 422


def test_assignment_still_requires_a_destination(client: TestClient) -> None:
    response = client.post(
        "/assignments",
        json=_request(
            {"assigned_group": None, "assigned_technician_id": None},
        ),
    )

    assert response.status_code == 422


def test_request_id_must_be_a_uuid(client: TestClient) -> None:
    payload = _request({"message": "Messaggio demo sufficientemente lungo."})
    payload["request_id"] = "not-a-uuid"

    response = client.post("/requester-communications", json=payload)

    assert response.status_code == 422


def test_request_id_is_returned_as_a_valid_uuid(client: TestClient) -> None:
    response = client.post(
        "/requester-communications",
        json=_request({"message": "Messaggio demo sufficientemente lungo."}),
    )

    assert UUID(response.json()["request_id"]) == UUID(REQUEST_ID)


def test_simulated_endpoints_are_not_exposed_by_the_portal() -> None:
    portal_paths = {
        route.path for route in portal_app.routes if hasattr(route, "path")
    }

    assert "/assignments" not in portal_paths
    assert "/requester-communications" not in portal_paths
    assert "/vendor-escalations" not in portal_paths
