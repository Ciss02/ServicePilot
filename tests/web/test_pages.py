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
                            title="Postazione demo in lavorazione",
                            description=(
                                "La postazione dimostrativa richiede una verifica hardware."
                            ),
                            requester_id=employee.id,
                            site_id=site.id,
                            service="Supporto postazione",
                            affected_users=1,
                            category=TicketCategory.DEVICES_AND_HARDWARE,
                            subcategory="Postazione di lavoro",
                            impact=Impact.MEDIUM,
                            urgency=Urgency.HIGH,
                            priority=Priority.P2,
                            assigned_group="Supporto workplace",
                            assigned_technician_id=technician.id,
                            status=TicketStatus.IN_PROGRESS,
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
    assert "Postazione demo in lavorazione" in response.text
    assert "Ticket riservato a un altro dipendente" not in response.text
    assert "In attesa di te" in response.text
    assert "Risolto" in response.text
    assert "3 richieste" in response.text
    assert 'href="/app?filter=active#ticket-list-title"' in response.text
    assert 'href="/app?filter=waiting#ticket-list-title"' in response.text
    assert 'href="/app?filter=completed#ticket-list-title"' in response.text


@pytest.mark.parametrize(
    ("selected_filter", "visible_titles", "hidden_titles", "expected_count"),
    [
        (
            "active",
            [
                "VPN demo in attesa di informazioni",
                "Postazione demo in lavorazione",
            ],
            ["Software demo installato"],
            "2 richieste di 3",
        ),
        (
            "waiting",
            ["VPN demo in attesa di informazioni"],
            ["Postazione demo in lavorazione", "Software demo installato"],
            "1 richiesta di 3",
        ),
        (
            "completed",
            ["Software demo installato"],
            [
                "VPN demo in attesa di informazioni",
                "Postazione demo in lavorazione",
            ],
            "1 richiesta di 3",
        ),
    ],
    ids=["active", "waiting", "completed"],
)
def test_summary_cards_filter_personal_ticket_list(
    web_client,
    selected_filter: str,
    visible_titles: list[str],
    hidden_titles: list[str],
    expected_count: str,
) -> None:
    client, _, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)

    response = client.get(f"/app?filter={selected_filter}")
    normalized_text = " ".join(response.text.split())

    assert response.status_code == 200
    assert expected_count in normalized_text
    assert "Filtro attivo" in response.text
    assert "Mostra tutti" in response.text
    for title in visible_titles:
        assert title in response.text
    for title in hidden_titles:
        assert title not in response.text
    assert "Ticket riservato a un altro dipendente" not in response.text


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


def test_employee_can_start_guided_ticket_intake(web_client) -> None:
    client, _, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)

    response = client.get("/app/new-ticket")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "Raccontaci cosa non funziona" in response.text
    assert 'action="/app/new-ticket/problem"' in response.text
    assert 'name="description"' in response.text
    assert 'name="title"' not in response.text
    assert 'href="/app/new-ticket"' in response.text
    assert 'aria-current="page"' in response.text


def test_guided_intake_reasks_for_invalid_problem_description(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    response = client.post(
        "/app/new-ticket/problem",
        data={"description": "Troppo"},
    )

    assert response.status_code == 422
    assert "Serve qualche dettaglio in più" in response.text
    assert "almeno 10 caratteri" in response.text
    assert 'aria-invalid="true"' in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


def test_guided_intake_asks_only_for_missing_essential_details(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        session.add(Site(code="INACTIVE-DEMO", name="Sede disattivata", is_active=False))
        session.commit()

    description = "La connessione VPN demo mostra un errore dopo l'accesso."
    response = client.post(
        "/app/new-ticket/problem",
        data={"description": description},
    )

    assert response.status_code == 200
    assert "La connessione VPN demo mostra un errore" in response.text
    assert "mi mancano quattro informazioni essenziali" in response.text
    assert 'name="description"' in response.text
    assert 'name="title"' in response.text
    assert 'name="site_id"' in response.text
    assert 'name="service"' in response.text
    assert 'name="affected_users"' in response.text
    assert "Sede Web Demo" in response.text
    assert "Sede disattivata" not in response.text


def test_guided_intake_rejects_invalid_or_inactive_details(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        inactive_site = Site(
            code="INACTIVE-FORGED-DEMO",
            name="Sede inattiva forzata",
            is_active=False,
        )
        session.add(inactive_site)
        session.commit()
        inactive_site_id = inactive_site.id
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    response = client.post(
        "/app/new-ticket/details",
        data={
            "description": "La connessione VPN demo mostra un errore dopo l'accesso.",
            "title": "VPN demo non disponibile",
            "site_id": str(inactive_site_id),
            "service": "VPN",
            "affected_users": "0",
        },
    )

    assert response.status_code == 422
    assert "Seleziona una sede disponibile" in response.text
    assert "compreso tra 1 e 10.000" in response.text
    assert "Il ticket non è ancora stato creato" not in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


def test_guided_intake_collects_data_without_creating_ticket(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        site_id = session.scalar(select(Site.id).where(Site.code == "WEB-DEMO"))
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    response = client.post(
        "/app/new-ticket/details",
        data={
            "description": "La connessione VPN demo mostra un errore dopo l'accesso.",
            "title": "VPN demo non disponibile",
            "site_id": str(site_id),
            "service": "Accesso remoto",
            "affected_users": "2",
        },
    )

    assert response.status_code == 200
    assert "Dati essenziali raccolti" in response.text
    assert "Il ticket non è ancora stato creato" in response.text
    assert "Controllo e conferma" in response.text
    assert "Con SP-043" in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


@pytest.mark.parametrize(
    "path",
    [
        "/app/new-ticket",
        "/app/new-ticket/problem",
        "/app/new-ticket/details",
    ],
)
def test_guided_intake_redirects_anonymous_visitor_to_login(
    web_client,
    path: str,
) -> None:
    client, _, _ = web_client
    method = client.get if path == "/app/new-ticket" else client.post

    response = method(path, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_guided_intake_is_not_available_to_technician(web_client) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)

    response = client.get("/app/new-ticket", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
