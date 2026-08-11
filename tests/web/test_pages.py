"""Test HTTP del layout, del login web e dell'area protetta."""

import re
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
                admin = User(
                    email="admin.web@servicepilot.example",
                    display_name="Amministratore Web Demo",
                    role=Role.ADMIN,
                    password_hash=hash_password(password),
                )
                site = Site(code="WEB-DEMO", name="Sede Web Demo")
                session.add_all(
                    [
                        employee,
                        other_employee,
                        empty_employee,
                        technician,
                        admin,
                        site,
                    ]
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


def ticket_confirmation_data(response_text: str, site_id: int) -> dict[str, str]:
    """Ricostruisce l'invio del riepilogo usando soltanto dati fittizi."""

    match = re.search(r'name="creation_key" value="([A-Za-z0-9_-]+)"', response_text)
    assert match is not None
    return {
        "description": "La connessione VPN demo mostra un errore dopo l'accesso.",
        "title": "VPN demo non disponibile",
        "site_id": str(site_id),
        "service": "Accesso remoto",
        "affected_users": "2",
        "creation_key": match.group(1),
    }


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


def test_technician_queue_lists_all_tickets_and_operational_filters(web_client) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)

    response = client.get("/app")

    assert response.status_code == 200
    assert "Coda tecnica" in response.text
    assert "VPN demo in attesa di informazioni" in response.text
    assert "Ticket riservato a un altro dipendente" in response.text
    assert "Applica filtri" in response.text
    assert "Da assegnare" in response.text
    assert "4 di 4" in response.text
    assert 'href="/app?status=open&sort=priority#technical-ticket-list"' in response.text
    assert 'href="/app?status=completed&sort=updated#technical-ticket-list"' in response.text
    assert '.technical-summary a[aria-current="true"]' in client.get(
        "/static/styles.css"
    ).text

    filtered = client.get("/app?status=new&assignment=unassigned&priority=pending")

    assert filtered.status_code == 200
    assert "Ticket riservato a un altro dipendente" in filtered.text
    assert "VPN demo in attesa di informazioni" not in filtered.text
    assert "1 di 4" in filtered.text


@pytest.mark.parametrize(
    ("query", "active_label"),
    [
        ("status=open&sort=priority", "ticket aperti"),
        ("assignment=unassigned&sort=priority", "ticket da assegnare"),
        ("status=waiting&sort=priority", "ticket in attesa"),
        ("status=completed&sort=updated", "ticket completati"),
    ],
)
def test_technical_summary_highlights_the_selected_filter(
    web_client,
    query: str,
    active_label: str,
) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)

    response = client.get(f"/app?{query}")
    current_link = re.search(
        rf'<a\s+href="[^"]+"\s+aria-current="true"\s+'
        rf'aria-label="[^"]*{active_label}[^"]*"',
        response.text,
    )

    assert response.status_code == 200
    assert current_link is not None


def test_admin_can_use_the_same_technical_queue(web_client) -> None:
    client, _, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)

    response = client.get("/app?assignment=unassigned")

    assert response.status_code == 200
    assert "Area tecnica" in response.text
    assert "Ticket riservato a un altro dipendente" in response.text


def test_technician_can_open_full_ticket_detail(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "Ticket riservato a un altro dipendente"
            )
        )

    response = client.get(f"/app/tickets/{ticket_id}")

    assert response.status_code == 200
    assert "Pannello operativo" in response.text
    assert "Altro Dipendente Web Demo" in response.text
    assert "Questa descrizione fittizia" in response.text
    assert 'action="/app/tickets/' in response.text
    assert 'value="in_progress"' in response.text
    assert 'value="resolved"' not in response.text
    assert "built-in method update" not in response.text


def test_technician_completes_a_ticket_lifecycle_from_the_web(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "Ticket riservato a un altro dipendente"
            )
        )
        technician_id = session.scalar(
            select(User.id).where(User.email == "tecnico.web@servicepilot.example")
        )

    in_progress = client.post(
        f"/app/tickets/{ticket_id}/update",
        data={
            "status": "in_progress",
            "assigned_technician_id": str(technician_id),
            "assigned_group": "Supporto workplace",
            "category": "devices_and_hardware",
            "subcategory": "Postazione demo",
            "impact": "high",
            "urgency": "high",
            "technician_note": "Presa in carico dal tecnico demo.",
            "resolution": "",
        },
        follow_redirects=False,
    )

    assert in_progress.status_code == 303
    assert in_progress.headers["location"].endswith("?updated=true")
    with Session(database_engine) as session:
        ticket = session.get(Ticket, ticket_id)
        assert ticket is not None
        assert ticket.status is TicketStatus.IN_PROGRESS
        assert ticket.assigned_technician_id == technician_id
        assert ticket.priority is Priority.P1

    resolved = client.post(
        f"/app/tickets/{ticket_id}/update",
        data={
            "status": "resolved",
            "assigned_technician_id": str(technician_id),
            "assigned_group": "Supporto workplace",
            "category": "devices_and_hardware",
            "subcategory": "Postazione demo",
            "impact": "high",
            "urgency": "high",
            "technician_note": "Verifica completata sul dispositivo fittizio.",
            "resolution": "Configurazione demo ripristinata e collaudo completato.",
        },
        follow_redirects=False,
    )

    assert resolved.status_code == 303
    with Session(database_engine) as session:
        ticket = session.get(Ticket, ticket_id)
        assert ticket is not None
        assert ticket.status is TicketStatus.RESOLVED
        assert "collaudo completato" in (ticket.resolution or "")

    closed = client.post(
        f"/app/tickets/{ticket_id}/update",
        data={
            "status": "closed",
            "assigned_technician_id": str(technician_id),
            "assigned_group": "Supporto workplace",
            "category": "devices_and_hardware",
            "subcategory": "Postazione demo",
            "impact": "high",
            "urgency": "high",
            "technician_note": "Verifica completata sul dispositivo fittizio.",
            "resolution": "Configurazione demo ripristinata e collaudo completato.",
        },
        follow_redirects=False,
    )

    assert closed.status_code == 303
    with Session(database_engine) as session:
        ticket = session.get(Ticket, ticket_id)
        assert ticket is not None
        assert ticket.status is TicketStatus.CLOSED


def test_technician_cannot_resolve_without_a_solution(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(Ticket.title == "Postazione demo in lavorazione")
        )

    response = client.post(
        f"/app/tickets/{ticket_id}/update",
        data={"status": "resolved"},
    )

    assert response.status_code == 422
    assert "Scrivi la soluzione" in response.text
    with Session(database_engine) as session:
        ticket = session.get(Ticket, ticket_id)
        assert ticket is not None
        assert ticket.status is TicketStatus.IN_PROGRESS


def test_employee_cannot_submit_technical_update(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(select(Ticket.id).limit(1))
        original_status = session.get(Ticket, ticket_id).status

    response = client.post(
        f"/app/tickets/{ticket_id}/update",
        data={"status": "in_progress"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    with Session(database_engine) as session:
        assert session.get(Ticket, ticket_id).status is original_status


def test_missing_technical_ticket_has_a_safe_not_found_page(web_client) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)

    response = client.get("/app/tickets/999")

    assert response.status_code == 404
    assert "Ticket non trovato" in response.text
    assert "Torna alla coda" in response.text


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


def test_guided_intake_shows_summary_without_creating_ticket(web_client) -> None:
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
    assert "Riepilogo della richiesta" in response.text
    assert "Il ticket non è ancora stato creato" in response.text
    assert "VPN demo non disponibile" in response.text
    assert "Sede Web Demo" in response.text
    assert "Accesso remoto" in response.text
    assert "Persone coinvolte" in response.text
    assert 'action="/app/new-ticket/confirm"' in response.text
    assert 'formaction="/app/new-ticket/edit"' in response.text
    assert 'href="/app">Annulla' in response.text
    assert 'name="confirmed" value="true"' in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


def test_employee_can_correct_summary_without_creating_ticket(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        site_id = session.scalar(select(Site.id).where(Site.code == "WEB-DEMO"))
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    response = client.post(
        "/app/new-ticket/edit",
        data={
            "description": "La connessione VPN demo mostra un errore dopo l'accesso.",
            "title": "VPN demo non disponibile",
            "site_id": str(site_id),
            "service": "Accesso remoto",
            "affected_users": "2",
        },
    )

    assert response.status_code == 200
    assert 'value="VPN demo non disponibile"' in response.text
    assert f'<option value="{site_id}" selected>' in response.text
    assert 'value="Accesso remoto"' in response.text
    assert 'value="2"' in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


def test_cancelling_summary_creates_nothing(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    response = client.get("/app")

    assert response.status_code == 200
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


def test_confirmation_creates_exactly_one_ticket(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        site_id = session.scalar(select(Site.id).where(Site.code == "WEB-DEMO"))
        requester_id = session.scalar(
            select(User.id).where(
                User.email == "dipendente.web@servicepilot.example"
            )
        )
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    summary = client.post(
        "/app/new-ticket/details",
        data={
            "description": "La connessione VPN demo mostra un errore dopo l'accesso.",
            "title": "VPN demo non disponibile",
            "site_id": str(site_id),
            "service": "Accesso remoto",
            "affected_users": "2",
        },
    )
    confirmation_data = ticket_confirmation_data(summary.text, site_id)
    confirmation_data["confirmed"] = "true"

    first_response = client.post(
        "/app/new-ticket/confirm",
        data=confirmation_data,
        follow_redirects=False,
    )
    second_response = client.post(
        "/app/new-ticket/confirm",
        data=confirmation_data,
        follow_redirects=False,
    )

    assert first_response.status_code == 303
    assert second_response.status_code == 303
    assert first_response.headers["location"] == second_response.headers["location"]
    assert first_response.headers["location"].endswith("?created=true")
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before + 1
        created_ticket = session.scalar(
            select(Ticket).where(Ticket.creation_key == confirmation_data["creation_key"])
        )
        assert created_ticket is not None
        assert created_ticket.requester_id == requester_id
        assert created_ticket.title == "VPN demo non disponibile"
        assert created_ticket.status is TicketStatus.NEW

    detail = client.get(first_response.headers["location"])
    assert detail.status_code == 200
    assert "Ticket creato correttamente" in detail.text


def test_missing_explicit_confirmation_creates_nothing(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        site_id = session.scalar(select(Site.id).where(Site.code == "WEB-DEMO"))
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    summary = client.post(
        "/app/new-ticket/details",
        data={
            "description": "La connessione VPN demo mostra un errore dopo l'accesso.",
            "title": "VPN demo non disponibile",
            "site_id": str(site_id),
            "service": "Accesso remoto",
            "affected_users": "2",
        },
    )
    confirmation_data = ticket_confirmation_data(summary.text, site_id)

    response = client.post("/app/new-ticket/confirm", data=confirmation_data)

    assert response.status_code == 422
    assert "deve essere confermata esplicitamente" in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


def test_confirmation_rechecks_that_site_is_still_active(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        site_id = session.scalar(select(Site.id).where(Site.code == "WEB-DEMO"))
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    summary = client.post(
        "/app/new-ticket/details",
        data={
            "description": "La connessione VPN demo mostra un errore dopo l'accesso.",
            "title": "VPN demo non disponibile",
            "site_id": str(site_id),
            "service": "Accesso remoto",
            "affected_users": "2",
        },
    )
    confirmation_data = ticket_confirmation_data(summary.text, site_id)
    confirmation_data["confirmed"] = "true"
    with Session(database_engine) as session:
        site = session.get(Site, site_id)
        assert site is not None
        site.is_active = False
        session.commit()

    response = client.post("/app/new-ticket/confirm", data=confirmation_data)

    assert response.status_code == 422
    assert "Seleziona una sede disponibile" in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


@pytest.mark.parametrize(
    "path",
    [
        "/app/new-ticket",
        "/app/new-ticket/problem",
        "/app/new-ticket/details",
        "/app/new-ticket/edit",
        "/app/new-ticket/confirm",
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


@pytest.mark.parametrize(
    "path",
    [
        "/app/new-ticket",
        "/app/new-ticket/problem",
        "/app/new-ticket/details",
        "/app/new-ticket/edit",
        "/app/new-ticket/confirm",
    ],
)
def test_guided_intake_is_not_available_to_technician(
    web_client,
    path: str,
) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    method = client.get if path == "/app/new-ticket" else client.post

    response = method(path, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
