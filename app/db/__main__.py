"""Comandi locali per inizializzare SQLite e caricare i dati demo."""

import argparse

from app.db.demo_data import load_demo_data
from app.db.session import create_database, database_url


def main() -> None:
    """Esegue il comando richiesto sul database configurato."""

    parser = argparse.ArgumentParser(
        prog="python -m app.db",
        description="Gestione del database ServicePilot",
    )
    parser.add_argument(
        "action",
        choices=("init", "seed"),
        default="init",
        nargs="?",
        help="init crea le tabelle; seed carica anche i dati dimostrativi",
    )
    args = parser.parse_args()

    if args.action == "seed":
        summary = load_demo_data()
        print(
            "Dataset demo pronto: "
            f"{summary.sites} sedi, {summary.users} utenti, "
            f"{summary.tickets} ticket ({database_url})"
        )
    else:
        create_database()
        print(f"Database inizializzato: {database_url}")


if __name__ == "__main__":
    main()
