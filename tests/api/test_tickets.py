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
                    Site(code="API-DEMO", name="Sede API Demo"),
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
