"""Connessione, sessioni e inizializzazione del database."""

import os
import sqlite3
from collections.abc import Callable, Iterator

from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.db.models  # noqa: F401  Registra le tabelle prima di crearle.


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
    user_columns = {
        column["name"] for column in inspect(target_engine).get_columns("users")
    }
    if "password_hash" not in user_columns:
        with target_engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
            )

    ticket_columns = {
        column["name"] for column in inspect(target_engine).get_columns("tickets")
    }
    if "creation_key" not in ticket_columns:
        with target_engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE tickets ADD COLUMN creation_key VARCHAR(64)")
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_tickets_creation_key "
                    "ON tickets (creation_key)"
                )
            )
            connection.execute(text("PRAGMA optimize"))


def get_session() -> Iterator[Session]:
    """Fornisce una sessione isolata e la chiude dopo ogni richiesta."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

