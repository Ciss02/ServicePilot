"""Connessione, sessioni e inizializzazione del database."""

import os
import sqlite3
from collections.abc import Callable, Iterator

from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

import app.db.models  # noqa: F401  Registra le tabelle prima di crearle.
from app.db.base import Base

DEFAULT_DATABASE_URL = "sqlite:///./servicepilot.db"
DATABASE_URL_ENV = "SERVICEPILOT_DATABASE_URL"


def build_engine(database_url: str) -> Engine:
    """Costruisce una connessione e abilita i riferimenti SQLite."""

    url: URL = make_url(database_url)
    connect_args = {"check_same_thread": False} if url.get_backend_name() == "sqlite" else {}
    database_engine = create_engine(url, connect_args=connect_args)

    if url.get_backend_name() == "sqlite":

        @event.listens_for(database_engine, "connect")
        def enable_foreign_keys(
            dbapi_connection: sqlite3.Connection,
            _connection_record: object,
        ) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


database_url = os.getenv(DATABASE_URL_ENV, DEFAULT_DATABASE_URL)
engine = build_engine(database_url)
SessionLocal: Callable[[], Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def create_database(target_engine: Engine = engine) -> None:
    """Crea le tabelle e applica i piccoli aggiornamenti compatibili previsti."""

    Base.metadata.create_all(target_engine)
    user_columns = {column["name"] for column in inspect(target_engine).get_columns("users")}
    if "password_hash" not in user_columns:
        with target_engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))

    ticket_columns = {column["name"] for column in inspect(target_engine).get_columns("tickets")}
    if "creation_key" not in ticket_columns:
        with target_engine.begin() as connection:
            connection.execute(text("ALTER TABLE tickets ADD COLUMN creation_key VARCHAR(64)"))
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_tickets_creation_key "
                    "ON tickets (creation_key)"
                )
            )
            connection.execute(text("PRAGMA optimize"))

    ticket_columns = {column["name"] for column in inspect(target_engine).get_columns("tickets")}
    if "classification_review_status" not in ticket_columns:
        with target_engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE tickets ADD COLUMN classification_review_status "
                    "VARCHAR(30) NOT NULL DEFAULT 'pending'"
                )
            )

    ticket_solution_migrations = {
        "ai_suggested_solution": ("ALTER TABLE tickets ADD COLUMN ai_suggested_solution TEXT"),
        "ai_solution_status": (
            "ALTER TABLE tickets ADD COLUMN ai_solution_status "
            "VARCHAR(30) NOT NULL DEFAULT 'pending'"
        ),
        "ai_solution_error": ("ALTER TABLE tickets ADD COLUMN ai_solution_error VARCHAR(300)"),
        "ai_solution_generated_at": (
            "ALTER TABLE tickets ADD COLUMN ai_solution_generated_at DATETIME"
        ),
    }
    ticket_columns = {column["name"] for column in inspect(target_engine).get_columns("tickets")}
    for column_name, statement in ticket_solution_migrations.items():
        if column_name not in ticket_columns:
            with target_engine.begin() as connection:
                connection.execute(text(statement))

    knowledge_document_columns = {
        column["name"] for column in inspect(target_engine).get_columns("knowledge_documents")
    }
    if "extraction_status" not in knowledge_document_columns:
        with target_engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE knowledge_documents ADD COLUMN extraction_status "
                    "VARCHAR(20) NOT NULL DEFAULT 'pending'"
                )
            )
    if "extraction_error" not in knowledge_document_columns:
        with target_engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE knowledge_documents ADD COLUMN extraction_error VARCHAR(300)")
            )

    knowledge_document_migrations = {
        "index_status": (
            "ALTER TABLE knowledge_documents ADD COLUMN index_status "
            "VARCHAR(20) NOT NULL DEFAULT 'pending'"
        ),
        "index_error": ("ALTER TABLE knowledge_documents ADD COLUMN index_error VARCHAR(300)"),
        "embedding_model": (
            "ALTER TABLE knowledge_documents ADD COLUMN embedding_model VARCHAR(120)"
        ),
        "embedding_dimensions": (
            "ALTER TABLE knowledge_documents ADD COLUMN embedding_dimensions INTEGER"
        ),
        "indexed_at": ("ALTER TABLE knowledge_documents ADD COLUMN indexed_at DATETIME"),
    }
    for column_name, statement in knowledge_document_migrations.items():
        if column_name not in knowledge_document_columns:
            with target_engine.begin() as connection:
                connection.execute(text(statement))

    knowledge_segment_columns = {
        column["name"] for column in inspect(target_engine).get_columns("knowledge_segments")
    }
    if "embedding_json" not in knowledge_segment_columns:
        with target_engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE knowledge_segments ADD COLUMN embedding_json TEXT")
            )

    proposed_action_migrations = {
        "reviewed_by_user_id": (
            "ALTER TABLE proposed_actions ADD COLUMN reviewed_by_user_id INTEGER"
        ),
        "decided_at": ("ALTER TABLE proposed_actions ADD COLUMN decided_at DATETIME"),
        "execution_reference": (
            "ALTER TABLE proposed_actions ADD COLUMN execution_reference VARCHAR(80)"
        ),
        "execution_message": ("ALTER TABLE proposed_actions ADD COLUMN execution_message TEXT"),
        "execution_error_code": (
            "ALTER TABLE proposed_actions ADD COLUMN execution_error_code VARCHAR(100)"
        ),
    }
    proposed_action_columns = {
        column["name"] for column in inspect(target_engine).get_columns("proposed_actions")
    }
    for column_name, statement in proposed_action_migrations.items():
        if column_name not in proposed_action_columns:
            with target_engine.begin() as connection:
                connection.execute(text(statement))
    with target_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_proposed_actions_reviewed_by_user_id "
                "ON proposed_actions (reviewed_by_user_id)"
            )
        )


def get_session() -> Iterator[Session]:
    """Fornisce una sessione isolata e la chiude dopo ogni richiesta."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
