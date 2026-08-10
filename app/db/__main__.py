"""Permette di inizializzare SQLite con ``python -m app.db``."""

from app.db.session import create_database, database_url


def main() -> None:
    """Crea le tabelle mancanti nel database configurato."""

    create_database()
    print(f"Database inizializzato: {database_url}")


if __name__ == "__main__":
    main()
