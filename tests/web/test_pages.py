"""Test HTTP del layout, del login web e dell'area protetta."""

import json
import re
import secrets
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.ai import AIUnavailableError
from app.ai.dependencies import get_ai_model, get_embedding_model
from app.actions import ActionExecutionResult
from app.actions.dependencies import get_action_service_client
from app.audit import record_action_proposed, record_ticket_created
from app.db import (
    AuthSession,
    AuditEvent,
    KnowledgeDocument,
    KnowledgeSegment,
    ProposedAction,
    Site,
    Ticket,
    TicketSolutionSource,
    User,
    build_engine,
    create_database,
    get_session,
)
from app.knowledge import KNOWLEDGE_STORAGE_DIRECTORY_ENV
from app.domain.vocabulary import (
    ActionStatus,
    ActionType,
    ClassificationReviewStatus,
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
def web_client(tmp_path, monkeypatch) -> Iterator[tuple[TestClient, Engine, str]]:
    """Avvia le pagine con un account fittizio e un database temporaneo."""

    password = secrets.token_urlsafe(18)
    monkeypatch.setenv(
        KNOWLEDGE_STORAGE_DIRECTORY_ENV,
        str(tmp_path / "knowledge-storage"),
    )
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
                session.flush()
                action_ticket = session.scalar(
                    select(Ticket).where(
                        Ticket.title == "VPN demo in attesa di informazioni"
                    )
                )
                proposed_action = ProposedAction(
                        ticket_id=action_ticket.id,
                        action_type=ActionType.NOTIFY_REQUESTER,
                        rationale=(
                            "Il richiedente attende un aggiornamento demo sulla verifica."
                        ),
                        payload_json=json.dumps(
                            {
                                "message": (
                                    "La verifica VPN demo è in corso. "
                                    "Ti aggiorneremo dopo il controllo."
                                )
                            },
                            ensure_ascii=False,
                        ),
                        expected_effect=(
                            "Registrare una comunicazione demo senza invii reali."
                        ),
                    )
                session.add(proposed_action)
                session.flush()
                record_ticket_created(session, action_ticket, employee)
                record_action_proposed(session, proposed_action)
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


class WebExtractionModelStub:
    """Modello locale per provare il percorso web senza usare Gemini."""

    def __init__(self, response: dict[str, object]) -> None:
        self.response = response

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema,
        system_instruction: str | None = None,
    ):
        del prompt, system_instruction
        return response_schema.model_validate(self.response)


class WebClassificationModelStub:
    """Proposta controllata per verificare la conferma web completa."""

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


class WebUnavailableModelStub:
    """Simula un timeout controllato durante la classificazione."""

    def generate_structured(self, **_kwargs):
        raise AIUnavailableError("timeout simulato")


class WebKeywordEmbeddingModel:
    """Indice locale prevedibile per provare il laboratorio senza Gemini."""

    model_name = "embedding-web-fittizio-v1"
    dimensions = 3

    @staticmethod
    def _vector(text: str) -> list[float]:
        normalized = text.casefold()
        if "vpn" in normalized or "connessione remota" in normalized:
            return [1.0, 0.0, 0.0]
        if "account" in normalized or "password" in normalized:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class WebSourcedSolutionModelStub:
    """Genera un suggerimento usando il primo passaggio recuperato."""

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema,
        system_instruction: str | None = None,
    ):
        assert "La decisione finale resta al tecnico" in (system_instruction or "")
        first_source = json.loads(prompt)["retrieved_sources"][0]
        return response_schema.model_validate(
            {
                "solution": (
                    "Disconnettere la VPN demo, attendere trenta secondi e "
                    "ripetere il collegamento verificandone la stabilità."
                ),
                "cited_source_ids": [first_source["source_id"]],
            }
        )


class WebSolutionModelThatMustNotRun:
    """Rende evidente se una fonte debole arriva per errore al modello."""

    def generate_structured(self, **_kwargs):
        raise AssertionError("Gemini non deve partire con fonti deboli")


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


def test_admin_can_open_knowledge_upload_page(web_client) -> None:
    client, _, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)

    response = client.get("/app/knowledge")

    assert response.status_code == 200
    assert "Carica un documento" in response.text
    assert "PDF e Markdown" in response.text
    assert "Dimensione massima: 5 MB" in response.text
    assert "Trova i passaggi pertinenti" in response.text
    assert 'name="q"' in response.text
    assert 'enctype="multipart/form-data"' in response.text
    assert 'aria-current="page"' in response.text


def test_admin_can_consult_and_filter_the_full_audit_log(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "VPN demo in attesa di informazioni"
            )
        )

    response = client.get("/app/audit")
    filtered = client.get(f"/app/audit?actor=ai&ticket_id={ticket_id}")

    assert response.status_code == 200
    assert "Audit log" in response.text
    assert "Sola lettura" in response.text
    assert "Ticket creato e confermato" in response.text
    assert "Nuova azione proposta dall&#39;assistente" in response.text
    assert "Richiedente Audit" not in response.text
    assert filtered.status_code == 200
    assert "Nuova azione proposta dall&#39;assistente" in filtered.text
    assert "Ticket creato e confermato" not in filtered.text
    assert 'aria-current="page"' in filtered.text


@pytest.mark.parametrize(
    "email",
    [
        "dipendente.web@servicepilot.example",
        "tecnico.web@servicepilot.example",
    ],
)
def test_non_admin_cannot_open_the_full_audit_log(web_client, email: str) -> None:
    client, _, password = web_client
    login_web(client, email, password)

    response = client.get("/app/audit", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/app"


@pytest.mark.parametrize(
    "email",
    [
        "dipendente.web@servicepilot.example",
        "tecnico.web@servicepilot.example",
    ],
)
def test_non_admin_cannot_open_or_upload_knowledge_documents(
    web_client,
    email: str,
) -> None:
    client, database_engine, password = web_client
    login_web(client, email, password)

    page = client.get("/app/knowledge", follow_redirects=False)
    upload = client.post(
        "/app/knowledge",
        files={"document": ("procedura.md", b"# Demo\n", "text/markdown")},
        follow_redirects=False,
    )

    assert page.status_code == 303
    assert page.headers["location"] == "/app"
    assert upload.status_code == 303
    assert upload.headers["location"] == "/app"
    with Session(database_engine) as session:
        assert session.scalar(
            select(func.count()).select_from(KnowledgeDocument)
        ) == 0


def test_admin_uploads_markdown_and_sees_it_in_the_library(
    web_client,
    tmp_path,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)

    response = client.post(
        "/app/knowledge",
        files={
            "document": (
                "procedura-wifi-demo.md",
                b"# Wi-Fi demo\n\nProcedura completamente fittizia.\n",
                "text/markdown",
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/app/knowledge?uploaded=true&extraction=ready&indexing=pending"
    )
    with Session(database_engine) as session:
        document = session.scalar(select(KnowledgeDocument))
        assert document is not None
        assert document.original_filename == "procedura-wifi-demo.md"
        assert document.content_type == "text/markdown"
        segments = session.scalars(
            select(KnowledgeSegment).where(
                KnowledgeSegment.document_id == document.id
            )
        ).all()
        assert len(segments) == 1
        assert segments[0].source_section == "Wi-Fi demo"
        stored_path = tmp_path / "knowledge-storage" / document.storage_filename
        assert stored_path.read_bytes().startswith(b"# Wi-Fi demo")

    page = client.get(response.headers["location"])
    assert page.status_code == 200
    assert "Documento elaborato correttamente" in page.text
    assert "procedura-wifi-demo.md" in page.text
    assert "Markdown" in page.text
    assert "1 segmento" in page.text
    assert "Da indicizzare" in page.text


def test_invalid_admin_upload_shows_error_and_changes_nothing(
    web_client,
    tmp_path,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)

    response = client.post(
        "/app/knowledge",
        files={
            "document": (
                "procedura-finta.pdf",
                b"questo non e un documento PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
    assert "Caricamento non eseguito" in response.text
    assert "non contiene un documento PDF" in response.text
    with Session(database_engine) as session:
        assert session.scalar(
            select(func.count()).select_from(KnowledgeDocument)
        ) == 0
    storage_directory = tmp_path / "knowledge-storage"
    assert not storage_directory.exists() or not list(storage_directory.iterdir())


def test_admin_sees_when_a_valid_document_has_no_text_to_segment(
    web_client,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)

    response = client.post(
        "/app/knowledge",
        files={
            "document": (
                "solo-titolo-demo.md",
                b"# Solo titolo demo\n",
                "text/markdown",
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/app/knowledge?uploaded=true&extraction=failed&indexing=pending"
    )
    page = client.get(response.headers["location"])
    assert "Documento conservato, testo non estratto" in page.text
    assert "Testo non estratto" in page.text
    with Session(database_engine) as session:
        document = session.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.original_filename == "solo-titolo-demo.md"
            )
        )
        assert document is not None
        assert document.extraction_status == "failed"
        assert session.scalar(
            select(func.count())
            .select_from(KnowledgeSegment)
            .where(KnowledgeSegment.document_id == document.id)
        ) == 0


def test_admin_search_finds_a_known_procedure_with_its_source(web_client) -> None:
    client, database_engine, password = web_client
    client.app.dependency_overrides[get_embedding_model] = WebKeywordEmbeddingModel
    login_web(client, "admin.web@servicepilot.example", password)

    vpn_upload = client.post(
        "/app/knowledge",
        files={
            "document": (
                "procedura-vpn-web-demo.md",
                b"# VPN demo\n\nChiudere e riaprire il client VPN fittizio.\n",
                "text/markdown",
            )
        },
        follow_redirects=False,
    )
    account_upload = client.post(
        "/app/knowledge",
        files={
            "document": (
                "procedura-account-web-demo.md",
                b"# Account demo\n\nAvviare lo sblocco della password fittizia.\n",
                "text/markdown",
            )
        },
        follow_redirects=False,
    )

    assert vpn_upload.headers["location"].endswith("indexing=ready")
    assert account_upload.headers["location"].endswith("indexing=ready")
    page = client.get(
        "/app/knowledge",
        params={"q": "La connessione remota VPN cade spesso"},
    )

    assert page.status_code == 200
    assert "procedura-vpn-web-demo.md" in page.text
    assert "VPN demo" in page.text
    assert "Chiudere e riaprire il client VPN fittizio" in page.text
    assert "Pertinenza 100%" in page.text
    assert page.text.index("procedura-vpn-web-demo.md") < page.text.index(
        "procedura-account-web-demo.md"
    )
    with Session(database_engine) as session:
        indexed_documents = session.scalars(
            select(KnowledgeDocument).where(KnowledgeDocument.index_status == "ready")
        ).all()
        assert len(indexed_documents) == 2
        assert all(document.embedding_model for document in indexed_documents)


def test_search_explains_when_embeddings_are_disabled(web_client) -> None:
    client, _, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)

    page = client.get(
        "/app/knowledge",
        params={"q": "Problema VPN fittizio"},
    )

    assert page.status_code == 200
    assert "Ricerca non disponibile" in page.text
    assert "ricerca semantica non è disponibile" in page.text


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


def test_technician_queue_defaults_to_open_tickets_and_operational_filters(
    web_client,
) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)

    response = client.get("/app")

    assert response.status_code == 200
    assert "Coda tecnica" in response.text
    assert "VPN demo in attesa di informazioni" in response.text
    assert "Ticket riservato a un altro dipendente" in response.text
    assert "Software demo installato" not in response.text
    assert "Applica filtri" in response.text
    assert "Da assegnare" in response.text
    assert "3 di 4" in response.text
    assert "Tutti gli stati" not in response.text
    assert "#technical-ticket-list" not in response.text
    assert (
        'href="/app?status=open&assignment=all&priority=all&sort=priority"'
        in response.text
    )
    assert (
        'href="/app?status=completed&assignment=all&priority=all&sort=priority"'
        in response.text
    )
    summary_markup = response.text.split('<div class="technical-summary"', 1)[1]
    summary_markup = summary_markup.split("</div>", 1)[0]
    assert summary_markup.count('aria-current="true"') == 1
    assert "ticket aperti" in summary_markup
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
        ("status=new&sort=priority", "ticket aperti"),
        ("status=open&assignment=unassigned&sort=priority", "ticket da assegnare"),
        ("status=waiting&sort=priority", "ticket in attesa"),
        ("status=closed&sort=updated", "ticket completati"),
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
    summary_markup = response.text.split('<div class="technical-summary"', 1)[1]
    summary_markup = summary_markup.split("</div>", 1)[0]
    assert summary_markup.count('aria-current="true"') == 1


def test_technical_summary_preserves_priority_and_sort_without_page_anchor(
    web_client,
) -> None:
    client, _, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)

    response = client.get("/app?status=open&priority=p2&sort=oldest")

    assert response.status_code == 200
    assert (
        'href="/app?status=waiting&assignment=all&priority=p2&sort=oldest"'
        in response.text
    )
    assert "#technical-ticket-list" not in response.text


def test_admin_can_use_the_same_technical_queue(web_client) -> None:
    client, _, password = web_client
    login_web(client, "admin.web@servicepilot.example", password)

    response = client.get("/app?assignment=unassigned")

    assert response.status_code == 200
    assert "Area tecnica" in response.text
    assert "Ticket riservato a un altro dipendente" in response.text


class WebActionServiceStub:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, proposal):
        self.calls.append(proposal)
        return ActionExecutionResult(
            succeeded=True,
            reference="COM-WEB-DEMO",
            message="Comunicazione demo registrata senza inviare messaggi reali.",
        )


def test_technician_sees_action_details_before_deciding(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "VPN demo in attesa di informazioni"
            )
        )

    response = client.get(f"/app/tickets/{ticket_id}")

    assert response.status_code == 200
    assert "Azioni proposte" in response.text
    assert "Approvazione obbligatoria" in response.text
    assert "Perché viene proposta" in response.text
    assert "Effetto previsto" in response.text
    assert "La verifica VPN demo è in corso" in response.text
    assert "Approva ed esegui" in response.text
    assert "Rifiuta proposta" in response.text
    assert "Cronologia del ticket" in response.text
    assert "Ticket creato e confermato" in response.text
    assert "Nuova azione proposta" in response.text


def test_technician_approval_calls_service_once_and_shows_result(web_client) -> None:
    client, database_engine, password = web_client
    service = WebActionServiceStub()
    client.app.dependency_overrides[get_action_service_client] = lambda: service
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        action = session.scalar(select(ProposedAction))
        ticket_id = action.ticket_id
        action_id = action.id

    response = client.post(
        f"/app/tickets/{ticket_id}/actions/{action_id}/decision",
        data={"decision": "approve"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("?action_result=succeeded")
    assert len(service.calls) == 1
    with Session(database_engine) as session:
        stored = session.get(ProposedAction, action_id)
        assert stored.status is ActionStatus.SUCCEEDED
        assert stored.execution_reference == "COM-WEB-DEMO"
        assert stored.reviewed_by_user_id is not None
        event_types = list(
            session.scalars(
                select(AuditEvent.event_type).where(
                    AuditEvent.ticket_id == ticket_id
                )
            ).all()
        )
        assert "action_approved" in event_types
        assert "action_execution_started" in event_types
        assert "action_execution_succeeded" in event_types

    detail = client.get(response.headers["location"])
    assert "Azione approvata e completata" in detail.text
    assert "Completata" in detail.text
    assert "COM-WEB-DEMO" in detail.text
    assert 'name="decision" value="approve"' not in detail.text


def test_web_rejection_never_calls_the_service(web_client) -> None:
    client, database_engine, password = web_client
    service = WebActionServiceStub()
    client.app.dependency_overrides[get_action_service_client] = lambda: service
    login_web(client, "admin.web@servicepilot.example", password)
    with Session(database_engine) as session:
        action = session.scalar(select(ProposedAction))
        ticket_id = action.ticket_id
        action_id = action.id

    response = client.post(
        f"/app/tickets/{ticket_id}/actions/{action_id}/decision",
        data={"decision": "reject"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("?action_result=rejected")
    assert service.calls == []
    with Session(database_engine) as session:
        assert session.get(ProposedAction, action_id).status is ActionStatus.REJECTED
        event_types = list(
            session.scalars(
                select(AuditEvent.event_type).where(
                    AuditEvent.ticket_id == ticket_id
                )
            ).all()
        )
        assert "action_rejected" in event_types
        assert "action_execution_started" not in event_types

    detail = client.get(response.headers["location"])
    assert "Nessun servizio è stato chiamato" in detail.text
    assert "Rifiutata" in detail.text


def test_employee_cannot_decide_a_proposed_action_from_the_web(web_client) -> None:
    client, database_engine, password = web_client
    service = WebActionServiceStub()
    client.app.dependency_overrides[get_action_service_client] = lambda: service
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        action = session.scalar(select(ProposedAction))
        ticket_id = action.ticket_id
        action_id = action.id

    response = client.post(
        f"/app/tickets/{ticket_id}/actions/{action_id}/decision",
        data={"decision": "approve"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    assert service.calls == []
    with Session(database_engine) as session:
        assert (
            session.get(ProposedAction, action_id).status
            is ActionStatus.PENDING_APPROVAL
        )


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


def test_technician_generates_sourced_solution_without_resolving_ticket(
    web_client,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    client.app.dependency_overrides[get_ai_model] = WebSourcedSolutionModelStub
    client.app.dependency_overrides[get_embedding_model] = WebKeywordEmbeddingModel
    with Session(database_engine) as session:
        ticket = session.scalar(
            select(Ticket).where(Ticket.title == "VPN demo in attesa di informazioni")
        )
        admin_id = session.scalar(
            select(User.id).where(User.email == "admin.web@servicepilot.example")
        )
        document = KnowledgeDocument(
            original_filename="accesso-vpn-demo.md",
            storage_filename="accesso-vpn-demo-web.md",
            content_type="text/markdown",
            size_bytes=180,
            checksum_sha256="b" * 64,
            extraction_status="ready",
            index_status="ready",
            embedding_model=WebKeywordEmbeddingModel.model_name,
            embedding_dimensions=WebKeywordEmbeddingModel.dimensions,
            uploaded_by_user_id=admin_id,
        )
        session.add(document)
        session.flush()
        segment = KnowledgeSegment(
            document_id=document.id,
            position=0,
            source_section="Accesso VPN demo > Nuovo tentativo",
            content=(
                "Disconnettere la VPN demo, attendere trenta secondi e riprovare "
                "controllando che il collegamento resti stabile."
            ),
            character_count=117,
            embedding_json=json.dumps([1.0, 0.0, 0.0]),
        )
        session.add(segment)
        session.commit()
        ticket_id = ticket.id

    response = client.post(
        f"/app/tickets/{ticket_id}/suggest-solution",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        f"/app/tickets/{ticket_id}?solution_attempted=true"
    )
    detail = client.get(response.headers["location"])
    assert detail.status_code == 200
    assert "Suggerimento tecnico con fonti" in detail.text
    assert "Suggerimento e fonti aggiornati" in detail.text
    assert "Disconnettere la VPN demo" in detail.text
    assert "accesso-vpn-demo.md" in detail.text
    assert "Accesso VPN demo &gt; Nuovo tentativo" in detail.text
    assert "Fonte 1" in detail.text
    assert "Decisione umana" in detail.text
    with Session(database_engine) as session:
        stored_ticket = session.get(Ticket, ticket_id)
        assert stored_ticket.resolution is None
        assert stored_ticket.ai_solution_status == "generated"
        assert session.scalar(select(TicketSolutionSource)) is not None


def test_employee_cannot_generate_ai_solution(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(select(Ticket.id).order_by(Ticket.id))

    response = client.post(
        f"/app/tickets/{ticket_id}/suggest-solution",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    with Session(database_engine) as session:
        ticket = session.get(Ticket, ticket_id)
        assert ticket.ai_solution_status == "pending"
        assert ticket.ai_suggested_solution is None


def test_technician_sees_prudent_message_for_weak_sources(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    client.app.dependency_overrides[get_ai_model] = WebSolutionModelThatMustNotRun
    client.app.dependency_overrides[get_embedding_model] = WebKeywordEmbeddingModel
    with Session(database_engine) as session:
        ticket = session.scalar(
            select(Ticket).where(
                Ticket.title == "Ticket riservato a un altro dipendente"
            )
        )
        admin_id = session.scalar(
            select(User.id).where(User.email == "admin.web@servicepilot.example")
        )
        document = KnowledgeDocument(
            original_filename="procedura-vpn-non-pertinente.md",
            storage_filename="procedura-vpn-non-pertinente-web.md",
            content_type="text/markdown",
            size_bytes=160,
            checksum_sha256="c" * 64,
            extraction_status="ready",
            index_status="ready",
            embedding_model=WebKeywordEmbeddingModel.model_name,
            embedding_dimensions=WebKeywordEmbeddingModel.dimensions,
            uploaded_by_user_id=admin_id,
        )
        session.add(document)
        session.flush()
        session.add(
            KnowledgeSegment(
                document_id=document.id,
                position=0,
                source_section="VPN demo",
                content="Riavviare la connessione VPN demo e verificarne la stabilità.",
                character_count=63,
                embedding_json=json.dumps([1.0, 0.0, 0.0]),
            )
        )
        session.commit()
        ticket_id = ticket.id

    response = client.post(
        f"/app/tickets/{ticket_id}/suggest-solution",
        follow_redirects=False,
    )

    assert response.status_code == 303
    detail = client.get(response.headers["location"])
    assert detail.status_code == 200
    assert "Nessuna soluzione generata" in detail.text
    assert "troppo poco pertinenti" in detail.text
    assert "Verifica i dettagli del ticket" in detail.text
    assert "aggiungi una procedura più specifica" in detail.text
    with Session(database_engine) as session:
        stored_ticket = session.get(Ticket, ticket_id)
        assert stored_ticket.ai_solution_status == "unavailable"
        assert stored_ticket.ai_suggested_solution is None
        assert stored_ticket.resolution is None
        assert session.scalar(select(TicketSolutionSource)) is None


@pytest.mark.parametrize(
    ("review_status", "expected_message"),
    [
        (ClassificationReviewStatus.AI_SUGGESTED, "Proposta AI · Da verificare"),
        (ClassificationReviewStatus.AI_UNAVAILABLE, "AI non disponibile"),
        (
            ClassificationReviewStatus.AI_INVALID_RESPONSE,
            "Risposta AI non utilizzabile",
        ),
    ],
)
def test_technical_detail_explains_ai_classification_state(
    web_client,
    review_status: ClassificationReviewStatus,
    expected_message: str,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket = session.scalar(
            select(Ticket).where(
                Ticket.title == "Ticket riservato a un altro dipendente"
            )
        )
        ticket.classification_review_status = review_status
        session.commit()
        ticket_id = ticket.id

    response = client.get(f"/app/tickets/{ticket_id}")

    assert response.status_code == 200
    assert expected_message in response.text
    assert 'name="review_classification" value="true"' in response.text


def test_technician_explicitly_reviews_and_corrects_classification(
    web_client,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "VPN demo in attesa di informazioni"
            )
        )

    response = client.post(
        f"/app/tickets/{ticket_id}/update",
        data={
            "status": "waiting_for_requester",
            "assigned_group": "Supporto rete",
            "category": "network_and_connectivity",
            "subcategory": "Accesso remoto",
            "impact": "high",
            "urgency": "medium",
            "technician_note": "Indicare un orario demo per la verifica.",
            "resolution": "",
            "review_classification": "true",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("?classification_reviewed=true")
    with Session(database_engine) as session:
        ticket = session.get(Ticket, ticket_id)
        assert ticket is not None
        assert ticket.subcategory == "Accesso remoto"
        assert ticket.priority is Priority.P2
        assert ticket.assigned_group == "Supporto rete"
        assert (
            ticket.classification_review_status
            is ClassificationReviewStatus.HUMAN_REVIEWED
        )

    detail = client.get(response.headers["location"])
    assert "Classificazione verificata" in detail.text
    assert "Verificata dal tecnico" in detail.text


def test_web_review_requires_complete_classification_and_group(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "tecnico.web@servicepilot.example", password)
    with Session(database_engine) as session:
        ticket_id = session.scalar(
            select(Ticket.id).where(
                Ticket.title == "Ticket riservato a un altro dipendente"
            )
        )

    response = client.post(
        f"/app/tickets/{ticket_id}/update",
        data={
            "status": "new",
            "category": "network_and_connectivity",
            "impact": "medium",
            "urgency": "medium",
            "assigned_group": "",
            "review_classification": "true",
        },
    )

    assert response.status_code == 422
    assert "Indica il gruppo prima di confermare" in response.text
    with Session(database_engine) as session:
        ticket = session.get(Ticket, ticket_id)
        assert ticket is not None
        assert (
            ticket.classification_review_status
            is ClassificationReviewStatus.PENDING
        )


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


def test_ai_extraction_goes_directly_to_confirmation_when_data_is_complete(
    web_client,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    with Session(database_engine) as session:
        tickets_before = session.scalar(select(func.count()).select_from(Ticket))

    client.app.dependency_overrides[get_ai_model] = lambda: WebExtractionModelStub(
        {
            "title": "VPN demo non disponibile",
            "site_code": "WEB-DEMO",
            "service": "Accesso remoto",
            "affected_users": 2,
        }
    )
    response = client.post(
        "/app/new-ticket/problem",
        data={
            "description": (
                "Nella Sede Web Demo la VPN non funziona per due persone."
            )
        },
    )

    assert response.status_code == 200
    assert "Riepilogo della richiesta" in response.text
    assert "VPN demo non disponibile" in response.text
    assert "Sede Web Demo" in response.text
    assert "Accesso remoto" in response.text
    assert "ticket non" in response.text
    assert "ancora stato creato" in response.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == tickets_before


def test_ai_extraction_asks_only_for_information_that_is_still_missing(
    web_client,
) -> None:
    client, _, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    client.app.dependency_overrides[get_ai_model] = lambda: WebExtractionModelStub(
        {
            "title": "Errore durante l'accesso VPN",
            "site_code": None,
            "service": "VPN",
            "affected_users": 1,
        }
    )

    response = client.post(
        "/app/new-ticket/problem",
        data={"description": "Quando accedo alla VPN compare un errore."},
    )

    assert response.status_code == 200
    assert "Mi serve ancora la sede interessata" in response.text
    assert '<select id="site_id" name="site_id"' in response.text
    assert '<input type="hidden" name="title"' in response.text
    assert '<input type="hidden" name="service" value="VPN">' in response.text
    assert '<input type="hidden" name="affected_users" value="1">' in response.text
    assert '<input id="title"' not in response.text
    assert '<input id="service"' not in response.text
    assert '<input id="affected_users"' not in response.text


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


def test_confirmation_saves_ai_classification_for_technical_review(
    web_client,
) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    client.app.dependency_overrides[get_ai_model] = WebClassificationModelStub
    with Session(database_engine) as session:
        site_id = session.scalar(select(Site.id).where(Site.code == "WEB-DEMO"))

    summary = client.post(
        "/app/new-ticket/details",
        data={
            "description": "La connessione VPN demo blocca due persone.",
            "title": "VPN demo non disponibile",
            "site_id": str(site_id),
            "service": "Accesso remoto",
            "affected_users": "2",
        },
    )
    confirmation_data = ticket_confirmation_data(summary.text, site_id)
    confirmation_data["confirmed"] = "true"
    response = client.post(
        "/app/new-ticket/confirm",
        data=confirmation_data,
        follow_redirects=False,
    )

    assert response.status_code == 303
    with Session(database_engine) as session:
        ticket = session.scalar(
            select(Ticket).where(
                Ticket.creation_key == confirmation_data["creation_key"]
            )
        )
        assert ticket is not None
        assert ticket.category is TicketCategory.NETWORK_AND_CONNECTIVITY
        assert ticket.subcategory == "VPN"
        assert ticket.impact is Impact.MEDIUM
        assert ticket.urgency is Urgency.HIGH
        assert ticket.priority is Priority.P2
        assert ticket.assigned_group == "Supporto rete"
        assert (
            ticket.classification_review_status
            is ClassificationReviewStatus.AI_SUGGESTED
        )


def test_ai_timeout_keeps_web_ticket_usable_for_manual_review(web_client) -> None:
    client, database_engine, password = web_client
    login_web(client, "dipendente.web@servicepilot.example", password)
    client.app.dependency_overrides[get_ai_model] = WebUnavailableModelStub
    with Session(database_engine) as session:
        site_id = session.scalar(select(Site.id).where(Site.code == "WEB-DEMO"))

    summary = client.post(
        "/app/new-ticket/details",
        data={
            "description": "La VPN demo non risponde durante il test del timeout.",
            "title": "VPN demo con timeout AI",
            "site_id": str(site_id),
            "service": "Accesso remoto",
            "affected_users": "2",
        },
    )
    confirmation_data = ticket_confirmation_data(summary.text, site_id)
    confirmation_data["confirmed"] = "true"
    response = client.post(
        "/app/new-ticket/confirm",
        data=confirmation_data,
        follow_redirects=False,
    )

    assert response.status_code == 303
    with Session(database_engine) as session:
        ticket = session.scalar(
            select(Ticket).where(
                Ticket.creation_key == confirmation_data["creation_key"]
            )
        )
        assert ticket is not None
        assert ticket.category is None
        assert (
            ticket.classification_review_status
            is ClassificationReviewStatus.AI_UNAVAILABLE
        )
        ticket_id = ticket.id

    client.post("/logout", follow_redirects=False)
    login_web(client, "tecnico.web@servicepilot.example", password)
    detail = client.get(f"/app/tickets/{ticket_id}")

    assert detail.status_code == 200
    assert "AI non disponibile" in detail.text
    assert "Completa manualmente" in detail.text


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
