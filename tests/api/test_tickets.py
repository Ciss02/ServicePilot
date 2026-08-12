"""Test HTTP delle API essenziali dei ticket."""

import secrets
from collections.abc import Iterator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.ai.dependencies import get_ai_model
from app.db import Site, Ticket, User, build_engine, create_database, get_session
from app.api.dependencies import require_roles
from app.domain.vocabulary import ClassificationReviewStatus, Priority, Role
from app.main import create_app
from app.security.passwords import hash_password


@pytest.fixture
def api_client(tmp_path) -> Iterator[tuple[TestClient, Engine, str]]:
    """Avvia l'app con dati minimi in un database temporaneo."""

    database_engine = build_engine(f"sqlite:///{tmp_path / 'ticket-api-test.db'}")
    password = secrets.token_urlsafe(18)

    def initialize_test_database() -> None:
        create_database(database_engine)
        with Session(database_engine) as session:
            session.add_all(
                [
                    User(
                        email="richiedente@servicepilot.example",
                        display_name="Richiedente API Demo",
                        role=Role.EMPLOYEE,
                        password_hash=hash_password(password),
                    ),
                    User(
                        email="tecnico@servicepilot.example",
                        display_name="Tecnico API Demo",
                        role=Role.TECHNICIAN,
                        password_hash=hash_password(password),
                    ),
                    User(
                        email="admin@servicepilot.example",
                        display_name="Admin API Demo",
                        role=Role.ADMIN,
                        password_hash=hash_password(password),
                    ),
                    User(
                        email="tecnico.inattivo@servicepilot.example",
                        display_name="Tecnico inattivo Demo",
                        role=Role.TECHNICIAN,
                        password_hash=hash_password(password),
                        is_active=False,
                    ),
                    User(
                        email="altro.dipendente@servicepilot.example",
                        display_name="Altro dipendente API Demo",
                        role=Role.EMPLOYEE,
                        password_hash=hash_password(password),
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
        login_response = client.post(
            "/auth/login",
            json={
                "email": "richiedente@servicepilot.example",
                "password": password,
            },
        )
        assert login_response.status_code == 200
        yield client, database_engine, password

    database_engine.dispose()


def valid_ticket_payload() -> dict[str, object]:
    return {
        "title": "Accesso VPN non disponibile",
        "description": "La VPN demo mostra un errore prima del collegamento.",
        "site_id": 1,
        "service": "Accesso remoto",
        "affected_users": 1,
        "confirmed": True,
    }


class APIClassificationModelStub:
    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema,
        system_instruction: str | None = None,
    ):
        del prompt, system_instruction
        return response_schema.model_validate(
            {
                "category": "network_and_connectivity",
                "subcategory": "VPN",
                "impact": "medium",
                "urgency": "high",
                "assigned_group": "Supporto rete",
            }
        )


def login_as(client: TestClient, email: str, password: str) -> None:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200


def login_as_technician(client: TestClient, password: str) -> None:
    login_as(client, "tecnico@servicepilot.example", password)


def test_create_ticket_saves_confirmed_request(api_client) -> None:
    client, database_engine, _ = api_client

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
    client, database_engine, _ = api_client
    payload = valid_ticket_payload()
    payload["confirmed"] = False

    response = client.post("/tickets", json=payload)

    assert response.status_code == 422
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 0


def test_create_ticket_saves_ai_suggestion_but_calculates_priority_in_backend(
    api_client,
) -> None:
    client, database_engine, _ = api_client
    client.app.dependency_overrides[get_ai_model] = APIClassificationModelStub

    response = client.post("/tickets", json=valid_ticket_payload())

    assert response.status_code == 201
    assert response.json()["category"] == "network_and_connectivity"
    assert response.json()["subcategory"] == "VPN"
    assert response.json()["impact"] == "medium"
    assert response.json()["urgency"] == "high"
    assert response.json()["priority"] == "p2"
    assert response.json()["assigned_group"] == "Supporto rete"
    assert response.json()["classification_review_status"] == "ai_suggested"
    with Session(database_engine) as session:
        saved = session.get(Ticket, response.json()["id"])
        assert saved is not None
        assert saved.priority is Priority.P2


def test_technician_corrects_and_confirms_ai_classification(api_client) -> None:
    client, database_engine, password = api_client
    client.app.dependency_overrides[get_ai_model] = APIClassificationModelStub
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)

    response = client.patch(
        f"/tickets/{ticket_id}",
        json={
            "classification": {
                "category": "account_and_access",
                "subcategory": "Accesso VPN",
                "impact": "low",
                "urgency": "medium",
            },
            "assigned_group": "Service desk",
            "classification_reviewed": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["category"] == "account_and_access"
    assert response.json()["priority"] == "p4"
    assert response.json()["classification_review_status"] == "human_reviewed"
    with Session(database_engine) as session:
        saved = session.get(Ticket, ticket_id)
        assert saved is not None
        assert (
            saved.classification_review_status
            is ClassificationReviewStatus.HUMAN_REVIEWED
        )


def test_technician_cannot_confirm_an_incomplete_classification(api_client) -> None:
    client, _, password = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)

    response = client.patch(
        f"/tickets/{ticket_id}",
        json={"classification_reviewed": True},
    )

    assert response.status_code == 422
    assert "Completa la classificazione" in response.json()["detail"]


@pytest.mark.parametrize(
    ("field", "missing_id", "expected_detail"),
    [("site_id", 999, "Sede 999 non trovata")],
)
def test_create_ticket_rejects_unknown_references(
    api_client,
    field: str,
    missing_id: int,
    expected_detail: str,
) -> None:
    client, database_engine, _ = api_client
    payload = valid_ticket_payload()
    payload[field] = missing_id

    response = client.post("/tickets", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 0


def test_list_tickets_returns_newest_first(api_client) -> None:
    client, _, _ = api_client
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
    client, _, _ = api_client
    created = client.post("/tickets", json=valid_ticket_payload()).json()

    response = client.get(f"/tickets/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_ticket_returns_404_when_missing(api_client) -> None:
    client, _, _ = api_client

    response = client.get("/tickets/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket 999 non trovato"}


def test_update_ticket_saves_allowed_fields(api_client) -> None:
    client, database_engine, password = api_client
    created = client.post("/tickets", json=valid_ticket_payload()).json()
    login_as_technician(client, password)

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
    client, _, password = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)

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
    client, _, password = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)

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
    client, _, password = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)
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
    client, _, password = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)

    response = client.patch(f"/tickets/{ticket_id}", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}


@pytest.mark.parametrize("user_id", [1, 4], ids=["employee", "inactive-technician"])
def test_update_ticket_rejects_ineligible_assignee(api_client, user_id: int) -> None:
    client, _, password = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)

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
    client, _, password = api_client
    created = client.post("/tickets", json=valid_ticket_payload()).json()
    login_as_technician(client, password)

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
    client, _, password = api_client
    ticket_id = client.post("/tickets", json=valid_ticket_payload()).json()["id"]
    login_as_technician(client, password)
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
    client, _, password = api_client
    login_as_technician(client, password)

    response = client.patch("/tickets/999", json={"status": "in_progress"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket 999 non trovato"}


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/tickets", valid_ticket_payload()),
        ("get", "/tickets", None),
        ("get", "/tickets/1", None),
        ("patch", "/tickets/1", {"title": "Titolo tecnico aggiornato"}),
    ],
    ids=["create", "list", "detail", "update"],
)
def test_ticket_endpoints_require_an_authenticated_session(
    api_client,
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    client, _, _ = api_client
    client.post("/auth/logout")

    response = client.request(method, path, json=payload)

    assert response.status_code == 401
    assert response.json() == {"detail": "Sessione non valida o scaduta"}


def test_requester_is_always_taken_from_the_authenticated_session(api_client) -> None:
    client, database_engine, _ = api_client
    payload = valid_ticket_payload()
    payload["requester_id"] = 5

    response = client.post("/tickets", json=payload)

    assert response.status_code == 422
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 0


@pytest.mark.parametrize(
    ("email", "expected_requester_id"),
    [
        ("tecnico@servicepilot.example", 2),
        ("admin@servicepilot.example", 3),
    ],
    ids=["technician", "admin"],
)
def test_each_role_can_create_only_its_own_ticket(
    api_client,
    email: str,
    expected_requester_id: int,
) -> None:
    client, _, password = api_client
    login_as(client, email, password)

    response = client.post("/tickets", json=valid_ticket_payload())

    assert response.status_code == 201
    assert response.json()["requester_id"] == expected_requester_id


def test_employee_lists_only_own_tickets_and_cannot_read_another_one(
    api_client,
) -> None:
    client, _, password = api_client
    own_ticket = client.post("/tickets", json=valid_ticket_payload()).json()
    login_as(client, "altro.dipendente@servicepilot.example", password)
    other_payload = valid_ticket_payload()
    other_payload["title"] = "Ticket del secondo dipendente demo"
    other_ticket = client.post("/tickets", json=other_payload).json()

    ticket_list = client.get("/tickets")
    hidden_detail = client.get(f"/tickets/{own_ticket['id']}")

    assert ticket_list.status_code == 200
    assert [ticket["id"] for ticket in ticket_list.json()] == [other_ticket["id"]]
    assert hidden_detail.status_code == 404
    assert hidden_detail.json() == {
        "detail": f"Ticket {own_ticket['id']} non trovato"
    }


def test_employee_cannot_use_technical_update(api_client) -> None:
    client, _, _ = api_client
    ticket = client.post("/tickets", json=valid_ticket_payload()).json()

    response = client.patch(
        f"/tickets/{ticket['id']}",
        json={"technician_note": "Nota che il dipendente non può aggiungere"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Operazione non consentita per il ruolo corrente"
    }


@pytest.mark.parametrize(
    "email",
    ["tecnico@servicepilot.example", "admin@servicepilot.example"],
    ids=["technician", "admin"],
)
def test_technical_roles_can_read_and_update_the_full_queue(
    api_client,
    email: str,
) -> None:
    client, _, password = api_client
    ticket = client.post("/tickets", json=valid_ticket_payload()).json()
    login_as(client, email, password)

    ticket_list = client.get("/tickets")
    ticket_detail = client.get(f"/tickets/{ticket['id']}")
    updated = client.patch(
        f"/tickets/{ticket['id']}",
        json={"technician_note": "Verifica autorizzata del ruolo tecnico"},
    )

    assert ticket_list.status_code == 200
    assert [item["id"] for item in ticket_list.json()] == [ticket["id"]]
    assert ticket_detail.status_code == 200
    assert updated.status_code == 200


def test_admin_only_control_accepts_admin_and_rejects_technician() -> None:
    admin_only = require_roles(Role.ADMIN)
    admin = User(
        id=1,
        email="admin.controllo@servicepilot.example",
        display_name="Admin Controllo Demo",
        role=Role.ADMIN,
    )
    technician = User(
        id=2,
        email="tecnico.controllo@servicepilot.example",
        display_name="Tecnico Controllo Demo",
        role=Role.TECHNICIAN,
    )

    assert admin_only(admin) is admin
    with pytest.raises(HTTPException) as error:
        admin_only(technician)

    assert error.value.status_code == 403
    assert error.value.detail == "Operazione non consentita per il ruolo corrente"
