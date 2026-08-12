"""Configurazione esterna e sicura del collegamento AI."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

AI_PROVIDER_ENV = "SERVICEPILOT_AI_PROVIDER"
AI_MODEL_ENV = "SERVICEPILOT_AI_MODEL"
AI_TIMEOUT_ENV = "SERVICEPILOT_AI_TIMEOUT_SECONDS"
AI_MAX_ATTEMPTS_ENV = "SERVICEPILOT_AI_MAX_ATTEMPTS"
AI_MAX_OUTPUT_TOKENS_ENV = "SERVICEPILOT_AI_MAX_OUTPUT_TOKENS"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

DEFAULT_AI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_MAX_OUTPUT_TOKENS = 1024


class AIProvider(StrEnum):
    """Provider disponibili nella configurazione dell'MVP."""

    DISABLED = "disabled"
    GEMINI = "gemini"


class AIConfigurationError(ValueError):
    """Segnala una configurazione AI assente o non sicura."""


@dataclass(frozen=True)
class AISettings:
    """Valori controllati necessari per costruire il provider scelto."""

    provider: AIProvider = AIProvider.DISABLED
    model: str = DEFAULT_AI_MODEL
    api_key: str | None = field(default=None, repr=False)
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise AIConfigurationError(f"{AI_MODEL_ENV} non può essere vuoto")
        if not 1 <= self.timeout_seconds <= 60:
            raise AIConfigurationError(f"{AI_TIMEOUT_ENV} deve essere compreso tra 1 e 60")
        if not 1 <= self.max_attempts <= 3:
            raise AIConfigurationError(f"{AI_MAX_ATTEMPTS_ENV} deve essere compreso tra 1 e 3")
        if not 64 <= self.max_output_tokens <= 4096:
            raise AIConfigurationError(
                f"{AI_MAX_OUTPUT_TOKENS_ENV} deve essere compreso tra 64 e 4096"
            )
        if self.provider is AIProvider.GEMINI and not self.api_key:
            raise AIConfigurationError(
                f"Variabile d'ambiente obbligatoria non configurata: {GEMINI_API_KEY_ENV}"
            )


def _read_integer(
    source: Mapping[str, str],
    variable_name: str,
    default: int,
) -> int:
    raw_value = source.get(variable_name, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError as error:
        raise AIConfigurationError(f"{variable_name} deve contenere un numero intero") from error


def load_ai_settings(
    environment: Mapping[str, str] | None = None,
) -> AISettings:
    """Legge la configurazione senza stampare o salvare la chiave API."""

    source = os.environ if environment is None else environment
    provider_value = source.get(AI_PROVIDER_ENV, AIProvider.DISABLED.value)
    try:
        provider = AIProvider(provider_value.strip().casefold())
    except ValueError as error:
        allowed = ", ".join(provider.value for provider in AIProvider)
        raise AIConfigurationError(f"{AI_PROVIDER_ENV} deve essere uno tra: {allowed}") from error

    api_key = source.get(GEMINI_API_KEY_ENV, "").strip() or None
    return AISettings(
        provider=provider,
        model=source.get(AI_MODEL_ENV, DEFAULT_AI_MODEL).strip(),
        api_key=api_key,
        timeout_seconds=_read_integer(
            source,
            AI_TIMEOUT_ENV,
            DEFAULT_TIMEOUT_SECONDS,
        ),
        max_attempts=_read_integer(
            source,
            AI_MAX_ATTEMPTS_ENV,
            DEFAULT_MAX_ATTEMPTS,
        ),
        max_output_tokens=_read_integer(
            source,
            AI_MAX_OUTPUT_TOKENS_ENV,
            DEFAULT_MAX_OUTPUT_TOKENS,
        ),
    )
