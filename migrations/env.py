"""Ambiente Alembic condiviso da CLI e avvio applicativo."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

import app.db.models  # noqa: F401  Registra tutte le tabelle nella metadata.
from app.db.base import Base

DATABASE_URL_ENV = "SERVICEPILOT_DATABASE_URL"

config = context.config
if config.config_file_name and config.get_section("loggers"):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
ENUM_CHECK_CONSTRAINT_NAMES = {
    "action_status",
    "action_type",
    "audit_actor_type",
    "audit_event_type",
    "classification_review_status",
    "impact",
    "priority",
    "role",
    "ticket_category",
    "ticket_status",
    "urgency",
}


def _include_schema_object(
    _object: object,
    name: str | None,
    object_type: str,
    reflected: bool,
    _compare_to: object,
) -> bool:
    """Ignora i soli falsi positivi degli enum riflessi come CHECK da SQLite."""

    return not (
        reflected and object_type == "check_constraint" and name in ENUM_CHECK_CONSTRAINT_NAMES
    )


def _database_url() -> str:
    """Usa la stessa configurazione database dell'applicazione."""

    return os.getenv(DATABASE_URL_ENV, config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Genera SQL senza aprire una connessione."""

    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=_include_schema_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=_include_schema_object,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Applica le revisioni tramite la connessione fornita o quella configurata."""

    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        _run_migrations(supplied_connection)
        return

    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        _run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
