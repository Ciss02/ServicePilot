"""Configurazione esterna delle password degli account dimostrativi."""

import os
from collections.abc import Mapping

from app.domain.vocabulary import Role

MIN_DEMO_PASSWORD_LENGTH = 12
DEMO_PASSWORD_ENV_BY_ROLE: dict[Role, str] = {
    Role.EMPLOYEE: "SERVICEPILOT_DEMO_EMPLOYEE_PASSWORD",
    Role.TECHNICIAN: "SERVICEPILOT_DEMO_TECHNICIAN_PASSWORD",
    Role.ADMIN: "SERVICEPILOT_DEMO_ADMIN_PASSWORD",
}


class DemoCredentialsError(ValueError):
    """Segnala una configurazione demo mancante o non sufficientemente sicura."""


def validate_demo_passwords(passwords: Mapping[Role, str]) -> dict[Role, str]:
    """Richiede una password abbastanza lunga per ciascuno dei tre ruoli."""

    validated: dict[Role, str] = {}
    for role, variable_name in DEMO_PASSWORD_ENV_BY_ROLE.items():
        password = passwords.get(role)
        if not isinstance(password, str) or not password:
            raise DemoCredentialsError(
                f"Variabile d'ambiente obbligatoria non configurata: {variable_name}"
            )
        if len(password) < MIN_DEMO_PASSWORD_LENGTH:
            raise DemoCredentialsError(
                f"{variable_name} deve contenere almeno {MIN_DEMO_PASSWORD_LENGTH} caratteri"
            )
        validated[role] = password
    return validated


def load_demo_passwords(
    environment: Mapping[str, str] | None = None,
) -> dict[Role, str]:
    """Legge le credenziali dall'ambiente senza stamparle o salvarle in chiaro."""

    source = os.environ if environment is None else environment
    configured = {
        role: source.get(variable_name, "")
        for role, variable_name in DEMO_PASSWORD_ENV_BY_ROLE.items()
    }
    return validate_demo_passwords(configured)
