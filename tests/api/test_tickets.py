"""Test HTTP delle API essenziali dei ticket."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.db import Site, Ticket, User, build_engine, create_database, get_session
from app.domain.vocabulary import Role
from app.main import create_app


@pytest.fixture
def api_client(tmp_path) -> Iterator[tuple[TestClient, Engine]]:
    """Avvia l'app con dati minimi in un database temporaneo."""

    database_engine = build_engine(f"sqlite:///{tmp_path / 'ticket-api-test.db'}")

    def initialize_test_database() -> None:
        create_database(database_engine)
        with Session(database_engine) as session:
            session.add_all(
                [
                    User(
                        email="richiedente@servicepilot.example",
                        display_name="Richiedente API Demo",
                        role=Role.EMPLOYEE,
                    ),
                    User(
                        email="tecnico@servicepilot.example",
                        display_name="Tecnico API Demo",
                        role=Role.TECHNICIAN,
                    ),
                    User(
                        email="admin@servicepilot.example",
                        display_name="Admin API Demo",
                        role=Role.ADMIN,
                    ),
                    User(
                        email="tecnico.inattivo@servicepilot.example",
                        display_name="Tecnico inattivo Demo",
                        role=Role.TECHNICIAN,
                        is_active=False,
                    ),
                    Site(code="API-DEMO", name="Sede API Demo"),
                    Site(code="API-DEMO-2", name="Seconda sede API Demo"),
                ]
            )
            session.commit()

    def override_session() -> Iterator[Session]:
        with Session(database_engine) as session:
            yield session

    test_app = create_app(database_initializer=initialize_test_database)
    test_app.dependency_overrides[get_session] = override_session

    with TestClient(test_app) as client:
        yield client, database_engine

    database_engine.dispose()


def valid_ticket_payload() -> dict[str, object]:
    return {
        "title": "Accesso VPN non disponibile",
        "description": "La VPN demo mostra un errore prima del collegamento.",
        "requester_id": 1,
        "site_id": 1,
        "service": "Accesso remoto",
        "affected_users": 1,
        "confirmed": True,
    }


def test_create_ticket_saves_confirmed_request(api_client) -> None:
    client, database_engine = api_client

    response = client.post("/tickets", json=valid_ticket_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Accesso VPN non disponibile"
    assert body["status"] == "new"
    assert body["category"] is None
    assert "confirmed" not in body
    assert body["created_at"]

    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 1


def test_create_ticket_requires_confirmation(api_client) -> None:
    client, database_engine = api_client
    payload = valid_ticket_payload()
    payload["confirmed"] = False

    response = client.post("/tickets", json=payload)

    assert response.status_code == 422
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 0


@pytest.mark.parametrize(
    ("field", "missing_id", "expected_detail"),
    [
        ("requester_id", 999, "Richiedente 999 non trovato"),
        ("site_id", 999, "Sede 999 non trovata"),
    ],
)
def test_create_ticket_rejects_unknown_references(
    api_client,
    field: str,
    missing_id: int,
    expected_detail: str,
) -> None:
    client, database_engine = api_client
    payload = valid_ticket_payload()
    payload[field] = missing_id

    response = client.post("/tickets", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 0


def test_list_tickets_returns_newest_first(api_client) -> None:
    client, _ = api_client
    first_payload = valid_ticket_payload()
    second_payload = valid_ticket_payload()
    second_payload["title"] = "Stampante demo non disponibile"

    first_response = client.post("/tickets", json=first_payload)
    second_response = client.post("/tickets", json=second_payload)
    response = client.get("/tickets")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert response.status_code == 200
    assert [ticket["id"] for ticket in response.json()] == [2, 1]


def test_get_ticket_returns_saved_detail(api_client) -> None:
    client, _ = api_client
    created = client.post("/tickets", json=valid_ticket_payload()).json()

    response = client.get(f"/tickets/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_ticket_returns_404_when_missing(api_client) -> None:
    client, _ = api_client

    response = client.get("/tickets/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket 999 non trovato"}


def test_update_ticket_saves_allowed_fields(api_client) -> None:
    client, database_engine = api_client
    created = client.post("/tickets", json=valid_ticket_payload()).json()

    response = client.patch(
        f"/tickets/{created['id']}",
        json={
            "title": "Accesso remoto da verificare",
            "site_id": 2,
            "service": "Connettività remota",
            "affected_users": 3,
            "technician_note": "Verifica tecnica avviata",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Accesso remoto da verificare"
    assert body["site_id"] == 2
    assert body["affected_users"] == 3
    assert body["requester_id"] == created["requester_id"]

    with Session(database_engine) as session:
        saved = session.get(Ticket, created["id"])
        assert saved is not None
        assert saved.technician_note == "Verifica tecnica avviata"


def test_update_ticket_recalculates_priority_from_classification(api_client) -> None:
    client, _ = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]

    response = client.patch(
        f"/tickets/{ticket_id}",
        json={
            "classification": {
                "category": "network_and_connectivity",
                "subcategory": "VPN",
                "impact": "high",
                "urgency": "medium",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["category"] == "network_and_connectivity"
    assert response.json()["priority"] == "p2"


@pytest.mark.parametrize("assignee_id", [2, 3], ids=["technician", "admin"])
def test_update_ticket_assigns_active_technician_and_starts_work(
    api_client, assignee_id: int
) -> None:
    client, _ = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]

    response = client.patch(
        f"/tickets/{ticket_id}",
        json={
            "assigned_group": "Supporto workplace",
            "assigned_technician_id": assignee_id,
            "status": "in_progress",
        },
    )

    assert response.status_code == 200
    assert response.json()["assigned_group"] == "Supporto workplace"
    assert response.json()["assigned_technician_id"] == assignee_id
    assert response.json()["status"] == "in_progress"


def test_update_ticket_resolves_and_closes_with_a_solution(api_client) -> None:
    client, _ = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    assert client.patch(
        f"/tickets/{ticket_id}", json={"status": "in_progress"}
    ).status_code == 200

    missing_resolution = client.patch(
        f"/tickets/{ticket_id}", json={"status": "resolved"}
    )
    resolved = client.patch(
        f"/tickets/{ticket_id}",
        json={
            "status": "resolved",
            "resolution": "Configurazione VPN demo corretta e collegamento verificato.",
        },
    )
    closed = client.patch(f"/tickets/{ticket_id}", json={"status": "closed"})

    assert missing_resolution.status_code == 422
    assert missing_resolution.json() == {
        "detail": "Per risolvere o chiudere il ticket è necessaria una soluzione"
    }
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"


@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        ({"site_id": 999}, "Sede 999 non trovata"),
        ({"assigned_technician_id": 999}, "Tecnico 999 non trovato"),
    ],
)
def test_update_ticket_rejects_unknown_references(
    api_client,
    payload: dict[str, object],
    expected_detail: str,
) -> None:
    client, _ = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]

    response = client.patch(f"/tickets/{ticket_id}", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}


@pytest.mark.parametrize("user_id", [1, 4], ids=["employee", "inactive-technician"])
def test_update_ticket_rejects_ineligible_assignee(api_client, user_id: int) -> None:
    client, _ = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]

    response = client.patch(
        f"/tickets/{ticket_id}", json={"assigned_technician_id": user_id}
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Il ticket può essere assegnato soltanto a un tecnico attivo"
    }


def test_update_ticket_rejects_forbidden_transition_without_partial_save(
    api_client,
) -> None:
    client, _ = api_client
    created = client.post("/tickets", json=valid_ticket_payload()).json()

    response = client.patch(
        f"/tickets/{created['id']}",
        json={
            "title": "Titolo che non deve essere salvato",
            "status": "waiting_for_vendor",
        },
    )
    saved = client.get(f"/tickets/{created['id']}").json()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Transizione da new a waiting_for_vendor non consentita"
    }
    assert saved["title"] == created["title"]
    assert saved["status"] == "new"


def test_update_ticket_treats_closed_status_as_final(api_client) -> None:
    client, _ = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    client.patch(f"/tickets/{ticket_id}", json={"status": "in_progress"})
    client.patch(
        f"/tickets/{ticket_id}",
        json={
            "status": "resolved",
            "resolution": "Configurazione demo corretta e verifica completata.",
        },
    )
    client.patch(f"/tickets/{ticket_id}", json={"status": "closed"})

    response = client.patch(
        f"/tickets/{ticket_id}", json={"status": "in_progress"}
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Transizione da closed a in_progress non consentita"
    }


def test_update_ticket_returns_404_when_missing(api_client) -> None:
    client, _ = api_client

    response = client.patch("/tickets/999", json={"status": "in_progress"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket 999 non trovato"}
