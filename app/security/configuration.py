"""Configurazione delle protezioni necessarie alla demo pubblica."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

PUBLIC_DEMO_ENV = "SERVICEPILOT_PUBLIC_DEMO"
SECURE_COOKIES_ENV = "SERVICEPILOT_SECURE_COOKIES"
ALLOWED_HOSTS_ENV = "SERVICEPILOT_ALLOWED_HOSTS"
LOGIN_ATTEMPTS_PER_MINUTE_ENV = "SERVICEPILOT_LOGIN_ATTEMPTS_PER_MINUTE"
DEFAULT_ALLOWED_HOSTS = ("127.0.0.1", "localhost", "testserver")
DEFAULT_LOGIN_ATTEMPTS_PER_MINUTE = 10


class SecurityConfigurationError(ValueError):
    """Segnala una configurazione che renderebbe insicura la demo pubblica."""


def _read_boolean(
    source: Mapping[str, str],
    variable_name: str,
    default: bool,
) -> bool:
    raw_value = source.get(variable_name, str(default)).strip().casefold()
    if raw_value in {"true", "1", "yes"}:
        return True
    if raw_value in {"false", "0", "no"}:
        return False
    raise SecurityConfigurationError(f"{variable_name} deve essere true oppure false")


@dataclass(frozen=True)
class SecuritySettings:
    """Scelte di sicurezza applicate all'intera applicazione web."""

    public_demo: bool = False
    secure_cookies: bool = False
    allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS
    login_attempts_per_minute: int = DEFAULT_LOGIN_ATTEMPTS_PER_MINUTE

    def __post_init__(self) -> None:
        if not self.allowed_hosts:
            raise SecurityConfigurationError(
                f"{ALLOWED_HOSTS_ENV} deve contenere almeno un nome host"
            )
        if self.public_demo and not self.secure_cookies:
            raise SecurityConfigurationError(
                f"{SECURE_COOKIES_ENV}=true \u00e8 obbligatorio quando {PUBLIC_DEMO_ENV}=true"
            )
        if self.public_demo and "*" in self.allowed_hosts:
            raise SecurityConfigurationError(
                f"{ALLOWED_HOSTS_ENV} non pu\u00f2 contenere * nella demo pubblica"
            )
        if not 1 <= self.login_attempts_per_minute <= 1_000:
            raise SecurityConfigurationError(
                f"{LOGIN_ATTEMPTS_PER_MINUTE_ENV} deve essere compreso tra 1 e 1000"
            )


def load_security_settings(
    environment: Mapping[str, str] | None = None,
) -> SecuritySettings:
    """Legge modalit\u00e0 demo, cookie HTTPS e host ammessi dall'ambiente."""

    source = os.environ if environment is None else environment
    raw_hosts = source.get(ALLOWED_HOSTS_ENV, ",".join(DEFAULT_ALLOWED_HOSTS))
    allowed_hosts = tuple(
        dict.fromkeys(host.strip() for host in raw_hosts.split(",") if host.strip())
    )
    raw_login_limit = source.get(
        LOGIN_ATTEMPTS_PER_MINUTE_ENV,
        str(DEFAULT_LOGIN_ATTEMPTS_PER_MINUTE),
    ).strip()
    try:
        login_attempts_per_minute = int(raw_login_limit)
    except ValueError as error:
        raise SecurityConfigurationError(
            f"{LOGIN_ATTEMPTS_PER_MINUTE_ENV} deve contenere un numero intero"
        ) from error

    return SecuritySettings(
        public_demo=_read_boolean(source, PUBLIC_DEMO_ENV, False),
        secure_cookies=_read_boolean(source, SECURE_COOKIES_ENV, False),
        allowed_hosts=allowed_hosts,
        login_attempts_per_minute=login_attempts_per_minute,
    )
