"""Avvio coordinato della demo pubblica e dei servizi azione simulati."""

import argparse
import os
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path

import uvicorn
from sqlalchemy.engine import make_url

from app.db.session import DATABASE_URL_ENV, DEFAULT_DATABASE_URL
from app.knowledge.configuration import (
    DEFAULT_KNOWLEDGE_STORAGE_DIRECTORY,
    KNOWLEDGE_STORAGE_DIRECTORY_ENV,
)

PORT_ENV = "PORT"
ACTION_SERVICE_PORT_ENV = "SERVICEPILOT_ACTION_SERVICE_PORT"
DEFAULT_PORT = 8000
DEFAULT_ACTION_SERVICE_PORT = 8011


class DeploymentConfigurationError(ValueError):
    """Segnala un valore di deploy non utilizzabile in modo sicuro."""


def _read_port(
    environment: Mapping[str, str],
    variable_name: str,
    default: int,
) -> int:
    raw_value = environment.get(variable_name, str(default)).strip()
    try:
        port = int(raw_value)
    except ValueError as error:
        raise DeploymentConfigurationError(
            f"{variable_name} deve contenere un numero intero"
        ) from error
    if not 1 <= port <= 65_535:
        raise DeploymentConfigurationError(f"{variable_name} deve essere compresa tra 1 e 65535")
    return port


def prepare_demo_directories(environment: Mapping[str, str] | None = None) -> None:
    """Crea le cartelle effimere prima di aprire SQLite o salvare documenti."""

    source = os.environ if environment is None else environment
    knowledge_directory = Path(
        source.get(
            KNOWLEDGE_STORAGE_DIRECTORY_ENV,
            str(DEFAULT_KNOWLEDGE_STORAGE_DIRECTORY),
        )
    )
    knowledge_directory.mkdir(parents=True, exist_ok=True)

    database_url = make_url(source.get(DATABASE_URL_ENV, DEFAULT_DATABASE_URL))
    if database_url.get_backend_name() != "sqlite" or not database_url.database:
        return
    if database_url.database == ":memory:":
        return
    Path(database_url.database).parent.mkdir(parents=True, exist_ok=True)


def build_simulator_command(port: int) -> list[str]:
    """Costruisce il comando del simulatore senza usare una shell."""

    return [
        sys.executable,
        "-m",
        "uvicorn",
        "app.simulated_services.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]


def wait_for_simulator(
    process: subprocess.Popen[bytes],
    port: int,
    *,
    timeout_seconds: float = 10,
) -> None:
    """Attende che il simulatore sia pronto o interrompe il deploy."""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Il servizio azioni simulato si è arrestato durante l'avvio")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Il servizio azioni simulato non è pronto entro il tempo previsto")


def run_public_demo(environment: Mapping[str, str] | None = None) -> None:
    """Prepara i dati demo e avvia portale e simulatore in una sola istanza."""

    source = os.environ if environment is None else environment
    portal_port = _read_port(source, PORT_ENV, DEFAULT_PORT)
    simulator_port = _read_port(
        source,
        ACTION_SERVICE_PORT_ENV,
        DEFAULT_ACTION_SERVICE_PORT,
    )
    if portal_port == simulator_port:
        raise DeploymentConfigurationError(
            "Il portale e il servizio azioni devono usare porte diverse"
        )

    prepare_demo_directories(source)

    # L'import avviene soltanto dopo la creazione della cartella che contiene SQLite.
    from app.db.demo_data import load_demo_data

    summary = load_demo_data()
    print(
        "Dataset demo pronto: "
        f"{summary.sites} sedi, {summary.users} utenti, {summary.tickets} ticket"
    )

    simulator = subprocess.Popen(build_simulator_command(simulator_port))
    try:
        wait_for_simulator(simulator, simulator_port)
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=portal_port,
            workers=1,
        )
    finally:
        simulator.terminate()
        try:
            simulator.wait(timeout=5)
        except subprocess.TimeoutExpired:
            simulator.kill()
            simulator.wait(timeout=5)


def main() -> None:
    """Espone un comando piccolo e ripetibile per la piattaforma di deploy."""

    parser = argparse.ArgumentParser(
        prog="python -m app.deployment",
        description="Avvia la demo pubblica ServicePilot",
    )
    parser.parse_args()
    run_public_demo()


if __name__ == "__main__":
    main()
