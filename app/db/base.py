"""Base condivisa da tutte le tabelle SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Registro centrale delle tabelle dell'applicazione."""

