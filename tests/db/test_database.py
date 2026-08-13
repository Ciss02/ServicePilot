"""Verifiche della struttura e delle migrazioni versionate del database."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Engine, String, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import Site, Ticket, User, build_engine, create_database
from app.db.base import Base
from app.db.migrations import CURRENT_REVISION, V010_TABLE_NAMES, DatabaseMigrationError
from app.domain.vocabulary import Role, TicketStatus

APPLICATION_TABLES = set(Base.metadata.tables)


@pytest.fixture
def database_engine(tmp_path: Path) -> Iterator[Engine]:
    """Usa un file SQLite temporaneo, isolato dai dati locali."""

    engine = build_engine(f"sqlite:///{tmp_path / 'servicepilot-test.db'}")
    yield engine
    engine.dispose()


def _normalized_sql(value: str | None) -> str | None:
    return " ".join(value.split()) if value is not None else None


def _schema_snapshot(engine: Engine) -> dict[str, object]:
    """Descrive lo schema applicativo senza includere la tabella tecnica Alembic."""

    database_inspector = inspect(engine)
    snapshot: dict[str, object] = {}
    for table_name in sorted(APPLICATION_TABLES):
        snapshot[table_name] = {
            "columns": sorted(
                (
                    column["name"],
                    str(column["type"]),
                    column["nullable"],
                    _normalized_sql(column.get("default")),
                    column["primary_key"],
                )
                for column in database_inspector.get_columns(table_name)
            ),
            "foreign_keys": sorted(
                (
                    tuple(constraint["constrained_columns"]),
                    constraint["referred_table"],
                    tuple(constraint["referred_columns"]),
                    constraint.get("options", {}).get("ondelete"),
                )
                for constraint in database_inspector.get_foreign_keys(table_name)
            ),
            "indexes": sorted(
                (
                    index["name"],
                    tuple(index["column_names"]),
                    bool(index["unique"]),
                )
                for index in database_inspector.get_indexes(table_name)
            ),
            "checks": sorted(
                (
                    constraint["name"],
                    _normalized_sql(constraint["sqltext"]),
                )
                for constraint in database_inspector.get_check_constraints(table_name)
            ),
            "unique_constraints": sorted(
                (
                    constraint["name"] or "",
                    tuple(constraint["column_names"]),
                )
                for constraint in database_inspector.get_unique_constraints(table_name)
            ),
        }
    return snapshot


def _create_populated_v010_database(
    engine: Engine,
    *,
    historical_alter_shape: bool = False,
) -> None:
    """Simula un database finale v0.1.0 privo della tabella Alembic."""

    Base.metadata.create_all(
        engine,
        tables=[table for table in Base.metadata.sorted_tables if table.name in V010_TABLE_NAMES],
    )
    if historical_alter_shape:
        with engine.begin() as connection:
            operations = Operations(MigrationContext.configure(connection))
            with operations.batch_alter_table("tickets", recreate="always") as batch_op:
                batch_op.drop_constraint(
                    "classification_review_status",
                    type_="check",
                )
                batch_op.drop_constraint(
                    "ck_tickets_ai_solution_status",
                    type_="check",
                )
                batch_op.alter_column(
                    "classification_review_status",
                    existing_type=String(length=19),
                    type_=String(length=30),
                    existing_nullable=False,
                    existing_server_default="pending",
                )
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users "
                "(id, email, display_name, role, is_active) VALUES "
                "(1, 'dipendente-migrazione@example.test', 'Dipendente Migrazione', "
                "'employee', 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sites (id, code, name, is_active) "
                "VALUES (1, 'MIGRATION-HQ', 'Sede migrazione', 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO tickets "
                "(id, title, description, requester_id, site_id, service, affected_users) "
                "VALUES (1, 'Ticket v0.1.0', 'Dato fittizio da conservare', 1, 1, 'VPN', 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO knowledge_documents "
                "(id, original_filename, storage_filename, content_type, size_bytes, "
                "checksum_sha256, uploaded_by_user_id) VALUES "
                "(1, 'procedura-demo.md', 'migration-demo.md', 'text/markdown', 20, "
                "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO knowledge_segments "
                "(id, document_id, position, source_section, content, character_count) "
                "VALUES (1, 1, 0, 'Test', 'Contenuto procedura demo', 23)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO proposed_actions "
                "(id, ticket_id, action_type, rationale, payload_json, expected_effect) "
                "VALUES (1, 1, 'notify_requester', "
                "'Motivazione fittizia sufficientemente lunga', '{}', "
                "'Effetto previsto fittizio')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO audit_events "
                "(id, ticket_id, actor_type, actor_user_id, event_type, summary, action_id) "
                "VALUES (1, 1, 'human', 1, 'ticket_created', "
                "'Ticket demo creato', 1)"
            )
        )


def test_fresh_database_creation_is_versioned_and_repeatable(database_engine: Engine) -> None:
    create_database(database_engine)
    create_database(database_engine)

    assert set(inspect(database_engine).get_table_names()) == APPLICATION_TABLES | {
        "alembic_version"
    }
    with database_engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == CURRENT_REVISION


def test_v010_upgrade_preserves_rows_and_records_baseline(database_engine: Engine) -> None:
    _create_populated_v010_database(database_engine)

    create_database(database_engine)
    create_database(database_engine)

    with database_engine.connect() as connection:
        assert connection.execute(text("SELECT email FROM users WHERE id = 1")).scalar_one() == (
            "dipendente-migrazione@example.test"
        )
        assert connection.execute(text("SELECT title FROM tickets WHERE id = 1")).scalar_one() == (
            "Ticket v0.1.0"
        )
        assert (
            connection.execute(
                text("SELECT original_filename FROM knowledge_documents WHERE id = 1")
            ).scalar_one()
            == "procedura-demo.md"
        )
        assert (
            connection.execute(text("SELECT summary FROM audit_events WHERE id = 1")).scalar_one()
            == "Ticket demo creato"
        )
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            CURRENT_REVISION
        )


def test_historical_v010_alter_shape_is_normalized_without_losing_rows(
    database_engine: Engine,
    tmp_path: Path,
) -> None:
    _create_populated_v010_database(database_engine, historical_alter_shape=True)
    fresh_engine = build_engine(f"sqlite:///{tmp_path / 'fresh-comparison.db'}")
    try:
        create_database(fresh_engine)
        create_database(database_engine)

        assert _schema_snapshot(database_engine) == _schema_snapshot(fresh_engine)
        with database_engine.connect() as connection:
            assert (
                connection.execute(text("SELECT title FROM tickets WHERE id = 1")).scalar_one()
                == "Ticket v0.1.0"
            )
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == CURRENT_REVISION
            )
    finally:
        fresh_engine.dispose()


def test_fresh_and_v010_upgrade_produce_the_same_application_schema(tmp_path: Path) -> None:
    fresh_engine = build_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
    upgraded_engine = build_engine(f"sqlite:///{tmp_path / 'upgraded.db'}")
    try:
        create_database(fresh_engine)
        _create_populated_v010_database(upgraded_engine)
        create_database(upgraded_engine)

        assert _schema_snapshot(fresh_engine) == _schema_snapshot(upgraded_engine)
    finally:
        fresh_engine.dispose()
        upgraded_engine.dispose()


def test_unknown_unversioned_schema_is_rejected_without_being_stamped(
    database_engine: Engine,
) -> None:
    with database_engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))

    with pytest.raises(DatabaseMigrationError, match="incompatibile"):
        create_database(database_engine)

    assert inspect(database_engine).get_table_names() == ["users"]


def test_initial_records_can_be_saved(database_engine: Engine) -> None:
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
    database_engine: Engine,
) -> None:
    create_database(database_engine)

    columns = {
        column["name"] for column in inspect(database_engine).get_columns("proposed_actions")
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


def test_ticket_rejects_unknown_requester(database_engine: Engine) -> None:
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
