"""Verifiche della struttura iniziale del database."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import Site, Ticket, User, build_engine, create_database
from app.domain.vocabulary import Role, TicketStatus


@pytest.fixture
def database_engine(tmp_path):
    """Usa un file SQLite temporaneo, isolato dai dati locali."""

    engine = build_engine(f"sqlite:///{tmp_path / 'servicepilot-test.db'}")
    yield engine
    engine.dispose()


def test_database_creation_is_repeatable(database_engine) -> None:
    create_database(database_engine)
    create_database(database_engine)

    assert set(inspect(database_engine).get_table_names()) == {
        "auth_sessions",
        "knowledge_documents",
        "knowledge_segments",
        "proposed_actions",
        "sites",
        "ticket_solution_sources",
        "tickets",
        "users",
    }
    assert "password_hash" in {
        column["name"] for column in inspect(database_engine).get_columns("users")
    }


def test_existing_user_table_receives_password_hash_column(database_engine) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE users ("
                "id INTEGER PRIMARY KEY, "
                "email VARCHAR(254) NOT NULL UNIQUE, "
                "display_name VARCHAR(120) NOT NULL, "
                "role VARCHAR(20) NOT NULL, "
                "is_active BOOLEAN NOT NULL, "
                "created_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO users "
                "(email, display_name, role, is_active, created_at) "
                "VALUES ('legacy@example.test', 'Profilo locale', "
                "'employee', 1, CURRENT_TIMESTAMP)"
            )
        )

    create_database(database_engine)
    create_database(database_engine)

    columns = {
        column["name"] for column in inspect(database_engine).get_columns("users")
    }
    with database_engine.connect() as connection:
        preserved_email, password_hash = connection.execute(
            text("SELECT email, password_hash FROM users")
        ).one()

    assert "password_hash" in columns
    assert preserved_email == "legacy@example.test"
    assert password_hash is None


def test_existing_ticket_table_receives_unique_creation_key(database_engine) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
        )
        connection.execute(
            text("INSERT INTO tickets (title) VALUES ('Ticket locale esistente')")
        )

    create_database(database_engine)
    create_database(database_engine)

    columns = {
        column["name"] for column in inspect(database_engine).get_columns("tickets")
    }
    indexes = {
        index["name"]: index for index in inspect(database_engine).get_indexes("tickets")
    }
    with database_engine.connect() as connection:
        preserved_title = connection.execute(text("SELECT title FROM tickets")).scalar_one()

    assert "creation_key" in columns
    assert indexes["ux_tickets_creation_key"]["unique"] == 1
    assert preserved_title == "Ticket locale esistente"


def test_existing_ticket_table_receives_classification_review_status(
    database_engine,
) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
        )
        connection.execute(
            text("INSERT INTO tickets (title) VALUES ('Ticket locale da conservare')")
        )

    create_database(database_engine)
    create_database(database_engine)

    columns = {
        column["name"] for column in inspect(database_engine).get_columns("tickets")
    }
    with database_engine.connect() as connection:
        title, review_status = connection.execute(
            text("SELECT title, classification_review_status FROM tickets")
        ).one()

    assert "classification_review_status" in columns
    assert title == "Ticket locale da conservare"
    assert review_status == "pending"


def test_existing_ticket_receives_ai_solution_columns(database_engine) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
        )
        connection.execute(
            text("INSERT INTO tickets (title) VALUES ('Ticket locale da conservare')")
        )

    create_database(database_engine)
    create_database(database_engine)

    columns = {
        column["name"] for column in inspect(database_engine).get_columns("tickets")
    }
    with database_engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT title, ai_suggested_solution, ai_solution_status, "
                "ai_solution_error, ai_solution_generated_at FROM tickets"
            )
        ).one()

    assert {
        "ai_suggested_solution",
        "ai_solution_status",
        "ai_solution_error",
        "ai_solution_generated_at",
    } <= columns
    assert row.title == "Ticket locale da conservare"
    assert row.ai_suggested_solution is None
    assert row.ai_solution_status == "pending"
    assert row.ai_solution_error is None
    assert row.ai_solution_generated_at is None


def test_existing_knowledge_document_receives_extraction_state(database_engine) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE knowledge_documents ("
                "id INTEGER PRIMARY KEY, original_filename VARCHAR(255) NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO knowledge_documents (original_filename) "
                "VALUES ('procedura-locale.md')"
            )
        )

    create_database(database_engine)
    create_database(database_engine)

    columns = {
        column["name"]
        for column in inspect(database_engine).get_columns("knowledge_documents")
    }
    with database_engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT original_filename, extraction_status, extraction_error, "
                "index_status, index_error, embedding_model, "
                "embedding_dimensions, indexed_at "
                "FROM knowledge_documents"
            )
        ).one()

    assert {
        "extraction_status",
        "extraction_error",
        "index_status",
        "index_error",
        "embedding_model",
        "embedding_dimensions",
        "indexed_at",
    } <= columns
    assert row.original_filename == "procedura-locale.md"
    assert row.extraction_status == "pending"
    assert row.extraction_error is None
    assert row.index_status == "pending"
    assert row.index_error is None
    assert row.embedding_model is None
    assert row.embedding_dimensions is None
    assert row.indexed_at is None


def test_existing_knowledge_segment_receives_embedding_column(database_engine) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE knowledge_segments (id INTEGER PRIMARY KEY)")
        )
        connection.execute(text("INSERT INTO knowledge_segments DEFAULT VALUES"))

    create_database(database_engine)
    create_database(database_engine)

    columns = {
        column["name"]
        for column in inspect(database_engine).get_columns("knowledge_segments")
    }
    with database_engine.connect() as connection:
        embedding_json = connection.execute(
            text("SELECT embedding_json FROM knowledge_segments")
        ).scalar_one()

    assert "embedding_json" in columns
    assert embedding_json is None


def test_initial_records_can_be_saved(database_engine) -> None:
    create_database(database_engine)

    with Session(database_engine) as session:
        requester = User(
            email="dipendente@example.test",
            display_name="Dipendente Demo",
            role=Role.EMPLOYEE,
        )
        site = Site(code="HQ", name="Sede centrale demo")
        session.add_all([requester, site])
        session.flush()

        ticket = Ticket(
            title="Accesso VPN non disponibile",
            description="Il collegamento VPN demo non completa la connessione.",
            requester_id=requester.id,
            site_id=site.id,
            service="VPN",
            affected_users=1,
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        assert ticket.id is not None
        assert ticket.status is TicketStatus.NEW
        assert ticket.category is None

    with database_engine.connect() as connection:
        stored_codes = connection.execute(
            text(
                "SELECT users.role, tickets.status "
                "FROM tickets JOIN users ON users.id = tickets.requester_id"
            )
        ).one()

    assert stored_codes == ("employee", "new")


def test_proposed_action_table_keeps_proposal_separate_from_ticket(
    database_engine,
) -> None:
    create_database(database_engine)

    columns = {
        column["name"]
        for column in inspect(database_engine).get_columns("proposed_actions")
    }
    assert columns == {
        "id",
        "ticket_id",
        "action_type",
        "rationale",
        "payload_json",
        "expected_effect",
        "status",
        "reviewed_by_user_id",
        "decided_at",
        "execution_reference",
        "execution_message",
        "execution_error_code",
        "created_at",
        "updated_at",
    }


def test_existing_proposed_actions_receive_decision_and_result_columns(
    database_engine,
) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE proposed_actions ("
                "id INTEGER PRIMARY KEY, "
                "ticket_id INTEGER NOT NULL, "
                "status VARCHAR(30) NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO proposed_actions (ticket_id, status) "
                "VALUES (7, 'pending_approval')"
            )
        )

    create_database(database_engine)
    create_database(database_engine)

    columns = {
        column["name"]
        for column in inspect(database_engine).get_columns("proposed_actions")
    }
    with database_engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT ticket_id, status, reviewed_by_user_id, decided_at, "
                "execution_reference, execution_message, execution_error_code "
                "FROM proposed_actions"
            )
        ).one()

    assert {
        "reviewed_by_user_id",
        "decided_at",
        "execution_reference",
        "execution_message",
        "execution_error_code",
    } <= columns
    assert row.ticket_id == 7
    assert row.status == "pending_approval"
    assert tuple(row)[2:] == (None, None, None, None, None)


def test_existing_database_receives_proposed_action_table(database_engine) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
        )
        connection.execute(
            text("INSERT INTO tickets (title) VALUES ('Ticket locale da conservare')")
        )

    create_database(database_engine)
    create_database(database_engine)

    assert "proposed_actions" in inspect(database_engine).get_table_names()
    with database_engine.connect() as connection:
        title = connection.execute(text("SELECT title FROM tickets")).scalar_one()
    assert title == "Ticket locale da conservare"


def test_ticket_rejects_unknown_requester(database_engine) -> None:
    create_database(database_engine)

    with Session(database_engine) as session:
        site = Site(code="STORE-01", name="Punto vendita demo")
        session.add(site)
        session.flush()
        session.add(
            Ticket(
                title="Stampante etichette non disponibile",
                description="La stampante demo non risponde al comando di stampa.",
                requester_id=999,
                site_id=site.id,
                service="Stampa etichette",
                affected_users=2,
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()

