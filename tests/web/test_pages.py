"""Test HTTP del layout, del login web e dell'area protetta."""

import secrets
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.db import (
    AuthSession,
    Site,
    Ticket,
    User,
    build_engine,
    create_database,
    get_session,
)
from app.domain.vocabulary import (
    Impact,
    Priority,
    Role,
    TicketCategory,
    TicketStatus,
    Urgency,
)
from app.main import create_app
from app.security.passwords import hash_password
from app.security.sessions import SESSION_COOKIE_NAME


@pytest.fixture
def web_client(tmp_path) -> Iterator[tuple[TestClient, Engine, str]]:
    """Avvia le pagine con un account fittizio e un database temporaneo."""

    password = secrets.token_urlsafe(18)
    database_engine = build_engine(f"sqlite:///{tmp_path / 'web-pages-test.db'}")

    def initialize_test_database() -> None:
        create_database(database_engine)
        with Session(database_engine) as session:
            if session.scalar(select(func.count()).select_from(User)) == 0:
                employee = User(
                    email="dipendente.web@servicepilot.example",
                    display_name="Dipendente Web Demo",
                    role=Role.EMPLOYEE,
                    password_hash=hash_password(password),
                )
                other_employee = User(
                    email="altro.dipendente.web@servicepilot.example",
                    display_name="Altro Dipendente Web Demo",
                    role=Role.EMPLOYEE,
                    password_hash=hash_password(password),
                )
                empty_employee = User(
                    email="senza.ticket.web@servicepilot.example",
                    display_name="Dipendente Senza Ticket Demo",
                    role=Role.EMPLOYEE,
                    password_hash=hash_password(password),
                )
                technician = User(
                    email="tecnico.web@servicepilot.example",
                    display_name="Tecnico Web Demo",
                    role=Role.TECHNICIAN,
                    password_hash=hash_password(password),
                )
                site = Site(code="WEB-DEMO", name="Sede Web Demo")
                session.add_all(
                    [employee, other_employee, empty_employee, technician, site]
                )
                session.flush()
                session.add_all(
                    [
                        Ticket(
                            title="VPN demo in attesa di informazioni",
                            description=(
                                "La connessione VPN demo si interrompe dopo pochi minuti."
                            ),
                            requester_id=employee.id,
                            site_id=site.id,
                            service="Accesso remoto",
                            affected_users=1,
                            category=TicketCategory.NETWORK_AND_CONNECTIVITY,
                            subcategory="VPN",
                            impact=Impact.MEDIUM,
                            urgency=Urgency.MEDIUM,
                            priority=Priority.P3,
                            assigned_group="Supporto workplace",
                            assigned_technician_id=technician.id,
                            status=TicketStatus.WAITING_FOR_REQUESTER,
                            technician_note="Indicare un orario demo per la verifica.",
                        ),
                        Ticket(
                            title="Software demo installato",
                            description=(
                                "Installazione richiesta per uno strumento grafico fittizio."
                            ),
                            requester_id=employee.id,
                            site_id=site.id,
                            service="Gestione software",
                            affected_users=1,
                            category=TicketCategory.SOFTWARE_AND_APPLICATIONS,
                            subcategory="Installazione software",
                            impact=Impact.LOW,
                            urgency=Urgency.LOW,
                            priority=Priority.P4,
                            assigned_group="Supporto workplace",
                            assigned_technician_id=technician.id,
                            status=TicketStatus.RESOLVED,
                            resolution="Applicazione demo installata e avvio verificato.",
                        ),
                        Ticket(
                            title="Ticket riservato a un altro dipendente",
                            description=(
                                "Questa descrizione fittizia non deve apparire altrove."
                            ),
                            requester_id=other_employee.id,
                            site_id=site.id,
                            service="Servizio riservato demo",
                            affected_users=1,
                            status=TicketStatus.NEW,
                        ),
                    ]
                )
                session.commit()

    def override_session() -> Iterator[Session]:
        with Session(database_engine) as session:
            yield session

    test_app = create_app(database_initializer=initialize_test_database)
    test_app.dependency_overrides[get_session] = override_session

    with TestClient(test_app) as client:
        yield client, database_engine, password

    database_engine.dispose()


def login_web(client: TestClient, email: str, password: str) -> None:
    response = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_login_page_has_accessible_responsive_structure(web_client) -> None:
    client, _, _ = web_client

    response = client.get("/login")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert '<html lang="it">' in response.text
    assert 'name="viewport"' in response.text
    assert 'for="email"' in response.text
    assert 'for="password"' in response.text
    assert 'autocomplete="current-password"' in response.text
    assert "Ambiente dimostrativo" in response.text
    assert "Entra in ServicePilot" in response.text


def test_static_styles_define_desktop_and_small_screen_layouts(web_client) -> None:
    client, _, _ = web_client

    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "grid-template-columns" in response.text
    assert "@media (max-width: 860px)" in response.text
    assert "@media (max-width: 620px)" in response.text
    assert "prefers-reduced-motion" in response.text


def test_protected_page_redirects_anonymous_visitor_to_login(web_client) -> None:
    client, _, _ = web_client

    response = client.get("/app", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_invalid_web_login_shows_generic_error_without_password(web_client) -> None:
    client, database_engine, _ = web_client
    wrong_password = secrets.token_urlsafe(18)

    response = client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": wrong_password,
        },
    )

    assert response.status_code == 401
    assert "Accesso non riuscito" in response.text
    assert "Controlla email e password" in response.text
    assert wrong_password not in response.text
    assert SESSION_COOKIE_NAME not in client.cookies
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_valid_web_login_opens_protected_area(web_client) -> None:
    client, database_engine, password = web_client

    response = client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    assert "HttpOnly" in response.headers["set-cookie"]
    assert SESSION_COOKIE_NAME in client.cookies

    protected_page = client.get("/app")
    assert protected_page.status_code == 200
    assert protected_page.headers["cache-control"] == "no-store"
    assert "Dipendente Web Demo" in protected_page.text
    assert "Dipendente" in protected_page.text
    assert "Le tue richieste" in protected_page.text
    assert "VPN demo in attesa di informazioni" in protected_page.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 1


def test_authenticated_visitor_is_redirected_away_from_login(web_client) -> None:
    client, _, password = web_client
    client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": password,
        },
    )

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/app"


def test_web_logout_revokes_session_and_returns_to_login(web_client) -> None:
    client, database_engine, password = web_client
    client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": password,
        },
    )

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert SESSION_COOKIE_NAME not in client.cookies
    assert client.get("/app", follow_redirects=False).status_code == 303
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_employee_dashboard_lists_only_personal_tickets(web_client) -> None:
    client, _, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)

    response = client.get("/app")

    assert response.status_code == 200
    assert "VPN demo in attesa di informazioni" in response.text
    assert "Software demo installato" in response.text
    assert "Ticket riservato a un altro dipendente" not in response.text
    assert "In attesa di te" in response.text
    assert "Risolto" in response.text
    assert "2 richieste" in response.text


def test_employee_can_open_own_ticket_detail(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "VPN demo in attesa di informazioni"
            )
        )

    response = client.get(f"/app/tickets/{ticket_id}")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "Descrizione del problema" in response.text
    assert "Sede Web Demo" in response.text
    assert "Rete e connettività" in response.text
    assert "Tecnico Web Demo" in response.text
    assert "Indicare un orario demo per la verifica" in response.text


def test_employee_cannot_open_another_employee_ticket(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        hidden_ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "Ticket riservato a un altro dipendente"
            )
        )

    response = client.get(f"/app/tickets/{hidden_ticket_id}")

    assert response.status_code == 404
    assert "Questo ticket non è tra le tue richieste" in response.text
    assert "Ticket riservato a un altro dipendente" not in response.text
    assert "Questa descrizione fittizia" not in response.text


def test_missing_ticket_uses_the_same_private_not_found_page(web_client) -> None:
    client, _, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)

    response = client.get("/app/tickets/999")

    assert response.status_code == 404
    assert "Potrebbe non esistere oppure appartenere a un altro account" in response.text


def test_employee_without_tickets_sees_an_empty_state(web_client) -> None:
    client, _, password = web_client
    login_web(client, "senza.ticket.web@servicepilot.example", password)

    response = client.get("/app")

    assert response.status_code == 200
    assert "Nessuna richiesta presente" in response.text
    assert "0 richieste" in response.text


def test_technician_keeps_placeholder_until_technical_queue_issue(web_client) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)

    response = client.get("/app")

    assert response.status_code == 200
    assert "Coda tecnica" in response.text
    assert "VPN demo in attesa di informazioni" not in response.text


def test_ticket_detail_redirects_anonymous_visitor_to_login(web_client) -> None:
    client, _, _ = web_client

    response = client.get("/app/tickets/1", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
