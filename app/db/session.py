"""Connessione, sessioni e inizializzazione del database."""

import os
import sqlite3
from collections.abc import Callable

from sqlalchemy import Engine, create_engine, event
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
    """Crea soltanto le tabelle mancanti; può essere richiamata più volte."""

    Base.metadata.create_all(target_engine)

