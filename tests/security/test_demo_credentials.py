"""Verifiche della configurazione esterna delle credenziali demo."""

import secrets

import pytest

from app.domain.vocabulary import Role
from app.security.demo_credentials import (
    DEMO_PASSWORD_ENV_BY_ROLE,
    DemoCredentialsError,
    load_demo_passwords,
)


def configured_environment() -> dict[str, str]:
    return {
        variable_name: secrets.token_urlsafe(24)
        for variable_name in DEMO_PASSWORD_ENV_BY_ROLE.values()
    }


def test_demo_passwords_are_loaded_for_all_roles() -> None:
    environment = configured_environment()

    passwords = load_demo_passwords(environment)

    assert set(passwords) == {Role.EMPLOYEE, Role.TECHNICIAN, Role.ADMIN}
    assert passwords[Role.EMPLOYEE] == environment[DEMO_PASSWORD_ENV_BY_ROLE[Role.EMPLOYEE]]


def test_missing_demo_password_is_rejected_without_exposing_values() -> None:
    environment = configured_environment()
    missing_variable = DEMO_PASSWORD_ENV_BY_ROLE[Role.ADMIN]
    environment.pop(missing_variable)

    with pytest.raises(DemoCredentialsError) as error:
        load_demo_passwords(environment)

    assert missing_variable in str(error.value)
    assert all(value not in str(error.value) for value in environment.values())


def test_short_demo_password_is_rejected() -> None:
    environment = configured_environment()
    variable_name = DEMO_PASSWORD_ENV_BY_ROLE[Role.TECHNICIAN]
    environment[variable_name] = secrets.token_urlsafe(3)

    with pytest.raises(DemoCredentialsError, match="almeno 12 caratteri"):
        load_demo_passwords(environment)
