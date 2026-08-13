"""Bootstrap sicuro delle migrazioni database versionate."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, Connection, Engine, inspect

import app.db.models  # noqa: F401  Registra lo schema v0.1.0 atteso.
from app.db.base import Base

ALEMBIC_VERSION_TABLE = "alembic_version"
BASELINE_REVISION = "0001_v010_baseline"
CURRENT_REVISION = "0003_support_groups"
V010_TABLE_NAMES = {
    "audit_events",
    "auth_sessions",
    "knowledge_documents",
    "knowledge_segments",
    "proposed_actions",
    "sites",
    "ticket_solution_sources",
    "tickets",
    "users",
}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIRECTORY = PROJECT_ROOT / "migrations"
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"


class DatabaseMigrationError(RuntimeError):
    """Segnala un database non riconoscibile senza modificarne lo schema."""


def _alembic_config(connection: Connection) -> Config:
    config = Config(str(ALEMBIC_CONFIG_PATH))
    config.set_main_option("script_location", str(MIGRATIONS_DIRECTORY))
    config.attributes["connection"] = connection
    return config


def _expected_foreign_keys(
    table_name: str,
) -> set[tuple[tuple[str, ...], str, tuple[str, ...], str | None]]:
    table = Base.metadata.tables[table_name]
    return {
        (
            tuple(column.name for column in constraint.columns),
            constraint.referred_table.name,
            tuple(element.column.name for element in constraint.elements),
            constraint.ondelete,
        )
        for constraint in table.foreign_key_constraints
    }


def _actual_foreign_keys(
    connection: Connection,
    table_name: str,
) -> set[tuple[tuple[str, ...], str, tuple[str, ...], str | None]]:
    return {
        (
            tuple(constraint["constrained_columns"]),
            constraint["referred_table"],
            tuple(constraint["referred_columns"]),
            constraint.get("options", {}).get("ondelete"),
        )
        for constraint in inspect(connection).get_foreign_keys(table_name)
    }


def _normalized_sql(value: str) -> str:
    return " ".join(value.split()).casefold()


def _expected_columns(
    connection: Connection,
    table_name: str,
) -> set[tuple[str, str, bool, bool]]:
    return {
        (
            column.name,
            str(column.type.compile(dialect=connection.dialect)).casefold(),
            column.nullable,
            column.primary_key,
        )
        for column in Base.metadata.tables[table_name].columns
    }


def _actual_columns(
    connection: Connection,
    table_name: str,
) -> set[tuple[str, str, bool, bool]]:
    return {
        (
            column["name"],
            str(column["type"]).casefold(),
            column["nullable"],
            bool(column["primary_key"]),
        )
        for column in inspect(connection).get_columns(table_name)
    }


def _expected_indexes(table_name: str) -> set[tuple[str, tuple[str, ...], bool]]:
    return {
        (
            index.name or "",
            tuple(column.name for column in index.columns),
            bool(index.unique),
        )
        for index in Base.metadata.tables[table_name].indexes
    }


def _actual_indexes(
    connection: Connection,
    table_name: str,
) -> set[tuple[str, tuple[str, ...], bool]]:
    return {
        (
            index["name"],
            tuple(index["column_names"]),
            bool(index["unique"]),
        )
        for index in inspect(connection).get_indexes(table_name)
    }


def _expected_unique_constraints(table_name: str) -> set[tuple[str, tuple[str, ...]]]:
    return {
        (
            constraint.name or "",
            tuple(column.name for column in constraint.columns),
        )
        for constraint in Base.metadata.tables[table_name].constraints
        if constraint.__visit_name__ == "unique_constraint"
    }


def _actual_unique_constraints(
    connection: Connection,
    table_name: str,
) -> set[tuple[str, tuple[str, ...]]]:
    return {
        (
            constraint["name"] or "",
            tuple(constraint["column_names"]),
        )
        for constraint in inspect(connection).get_unique_constraints(table_name)
    }


def _expected_checks(connection: Connection, table_name: str) -> set[tuple[str, str]]:
    return {
        (
            constraint.name or "",
            _normalized_sql(
                str(
                    constraint.sqltext.compile(
                        dialect=connection.dialect,
                        compile_kwargs={"literal_binds": True},
                    )
                ).replace(f"{table_name}.", "")
            ),
        )
        for constraint in Base.metadata.tables[table_name].constraints
        if isinstance(constraint, CheckConstraint)
    }


def _actual_checks(connection: Connection, table_name: str) -> set[tuple[str, str]]:
    return {
        (
            constraint["name"] or "",
            _normalized_sql(constraint["sqltext"]),
        )
        for constraint in inspect(connection).get_check_constraints(table_name)
    }


def _validate_v010_schema(connection: Connection) -> None:
    """Accetta soltanto una baseline v0.1.0 completa prima dello stamp."""

    database_inspector = inspect(connection)
    expected_tables = V010_TABLE_NAMES
    actual_tables = set(database_inspector.get_table_names())
    if actual_tables != expected_tables:
        missing = sorted(expected_tables - actual_tables)
        unexpected = sorted(actual_tables - expected_tables)
        raise DatabaseMigrationError(
            "Database non versionato incompatibile con ServicePilot v0.1.0: "
            f"tabelle mancanti={missing}, tabelle inattese={unexpected}"
        )

    for table_name in sorted(expected_tables):
        actual_columns = _actual_columns(connection, table_name)
        expected_columns = _expected_columns(connection, table_name)
        known_legacy_ticket_columns = (
            table_name == "tickets"
            and actual_columns - expected_columns
            == {("classification_review_status", "varchar(30)", False, False)}
            and expected_columns - actual_columns
            == {("classification_review_status", "varchar(19)", False, False)}
        )
        if actual_columns != expected_columns and not known_legacy_ticket_columns:
            raise DatabaseMigrationError(
                "Database non versionato incompatibile con ServicePilot v0.1.0: "
                f"colonne diverse nella tabella {table_name}"
            )
        if _actual_foreign_keys(connection, table_name) != _expected_foreign_keys(table_name):
            raise DatabaseMigrationError(
                "Database non versionato incompatibile con ServicePilot v0.1.0: "
                f"riferimenti diversi nella tabella {table_name}"
            )
        if _actual_indexes(connection, table_name) != _expected_indexes(table_name):
            raise DatabaseMigrationError(
                "Database non versionato incompatibile con ServicePilot v0.1.0: "
                f"indici diversi nella tabella {table_name}"
            )
        if _actual_unique_constraints(connection, table_name) != _expected_unique_constraints(
            table_name
        ):
            raise DatabaseMigrationError(
                "Database non versionato incompatibile con ServicePilot v0.1.0: "
                f"vincoli unici diversi nella tabella {table_name}"
            )
        actual_checks = _actual_checks(connection, table_name)
        expected_checks = _expected_checks(connection, table_name)
        known_legacy_ticket_checks = (
            table_name == "tickets"
            and not actual_checks - expected_checks
            and expected_checks - actual_checks
            == {
                (
                    "classification_review_status",
                    "classification_review_status in ('pending', 'ai_suggested', "
                    "'human_reviewed', 'ai_unavailable', 'ai_invalid_response')",
                ),
                (
                    "ck_tickets_ai_solution_status",
                    "ai_solution_status in ('pending', 'generated', 'unavailable', "
                    "'invalid_response')",
                ),
            }
        )
        if actual_checks != expected_checks and not known_legacy_ticket_checks:
            raise DatabaseMigrationError(
                "Database non versionato incompatibile con ServicePilot v0.1.0: "
                f"vincoli di controllo diversi nella tabella {table_name}"
            )


def upgrade_database(target_engine: Engine) -> None:
    """Porta un database vuoto o v0.1.0 all'ultima revisione in modo ripetibile."""

    with target_engine.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        foreign_keys_were_enabled = False
        if is_sqlite:
            foreign_keys_were_enabled = bool(
                connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
            )
            connection.commit()
            if foreign_keys_were_enabled:
                connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
                connection.commit()

        try:
            with connection.begin():
                table_names = set(inspect(connection).get_table_names())
                config = _alembic_config(connection)
                if table_names and ALEMBIC_VERSION_TABLE not in table_names:
                    _validate_v010_schema(connection)
                    command.stamp(config, BASELINE_REVISION)
                command.upgrade(config, "head")

            if is_sqlite:
                violations = connection.exec_driver_sql("PRAGMA foreign_key_check").all()
                connection.commit()
                if violations:
                    raise DatabaseMigrationError(
                        "La migrazione ha prodotto riferimenti SQLite non validi"
                    )
        finally:
            if connection.in_transaction():
                connection.rollback()
            if is_sqlite and foreign_keys_were_enabled:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()
