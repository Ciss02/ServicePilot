"""Controlli della preparazione usata dalla demo pubblica."""

from pathlib import Path

import pytest

from app.deployment import (
    ACTION_SERVICE_PORT_ENV,
    PORT_ENV,
    DeploymentConfigurationError,
    _read_port,
    build_simulator_command,
    prepare_demo_directories,
)


def test_prepare_demo_directories_creates_database_and_knowledge_parents(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "data" / "servicepilot.db"
    knowledge_path = tmp_path / "data" / "knowledge"

    prepare_demo_directories(
        {
            "SERVICEPILOT_DATABASE_URL": f"sqlite:///{database_path.as_posix()}",
            "SERVICEPILOT_KNOWLEDGE_STORAGE_DIR": str(knowledge_path),
        }
    )

    assert database_path.parent.is_dir()
    assert knowledge_path.is_dir()


def test_simulator_uses_localhost_and_never_exposes_its_port() -> None:
    command = build_simulator_command(8011)

    assert command[-4:] == ["--host", "127.0.0.1", "--port", "8011"]


@pytest.mark.parametrize("value", ["not-a-number", "0", "65536"])
def test_invalid_deploy_port_is_rejected(value: str) -> None:
    with pytest.raises(DeploymentConfigurationError):
        _read_port({PORT_ENV: value}, PORT_ENV, 8000)


def test_portal_and_simulator_have_independent_environment_names() -> None:
    assert PORT_ENV != ACTION_SERVICE_PORT_ENV
