"""Configurazione separata e sicura degli embedding della knowledge base."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from app.ai.configuration import (
    AI_MAX_ATTEMPTS_ENV,
    AI_TIMEOUT_ENV,
    GEMINI_API_KEY_ENV,
    AIConfigurationError,
    AIProvider,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_TIMEOUT_SECONDS,
)


EMBEDDING_PROVIDER_ENV = "SERVICEPILOT_EMBEDDING_PROVIDER"
EMBEDDING_MODEL_ENV = "SERVICEPILOT_EMBEDDING_MODEL"
EMBEDDING_DIMENSIONS_ENV = "SERVICEPILOT_EMBEDDING_DIMENSIONS"

DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_EMBEDDING_DIMENSIONS = 768


@dataclass(frozen=True)
class EmbeddingSettings:
    """Valori controllati necessari per costruire il provider degli embedding."""

    provider: AIProvider = AIProvider.DISABLED
    model: str = DEFAULT_EMBEDDING_MODEL
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    api_key: str | None = field(default=None, repr=False)
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_attempts: int = DEFAULT_MAX_ATTEMPTS

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise AIConfigurationError(f"{EMBEDDING_MODEL_ENV} non può essere vuoto")
        if not 128 <= self.dimensions <= 3072:
            raise AIConfigurationError(
                f"{EMBEDDING_DIMENSIONS_ENV} deve essere compreso tra 128 e 3072"
            )
        if not 1 <= self.timeout_seconds <= 60:
            raise AIConfigurationError(
                f"{AI_TIMEOUT_ENV} deve essere compreso tra 1 e 60"
            )
        if not 1 <= self.max_attempts <= 3:
            raise AIConfigurationError(
                f"{AI_MAX_ATTEMPTS_ENV} deve essere compreso tra 1 e 3"
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
        raise AIConfigurationError(
            f"{variable_name} deve contenere un numero intero"
        ) from error


def load_embedding_settings(
    environment: Mapping[str, str] | None = None,
) -> EmbeddingSettings:
    """Legge modello e limiti senza stampare o salvare la chiave API."""

    source = os.environ if environment is None else environment
    provider_value = source.get(
        EMBEDDING_PROVIDER_ENV,
        AIProvider.DISABLED.value,
    )
    try:
        provider = AIProvider(provider_value.strip().casefold())
    except ValueError as error:
        allowed = ", ".join(provider.value for provider in AIProvider)
        raise AIConfigurationError(
            f"{EMBEDDING_PROVIDER_ENV} deve essere uno tra: {allowed}"
        ) from error

    return EmbeddingSettings(
        provider=provider,
        model=source.get(EMBEDDING_MODEL_ENV, DEFAULT_EMBEDDING_MODEL).strip(),
        dimensions=_read_integer(
            source,
            EMBEDDING_DIMENSIONS_ENV,
            DEFAULT_EMBEDDING_DIMENSIONS,
        ),
        api_key=source.get(GEMINI_API_KEY_ENV, "").strip() or None,
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
    )
