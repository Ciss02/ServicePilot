"""Limiti locali condivisi per le chiamate ai provider AI della demo."""

from __future__ import annotations

import os
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from threading import Lock

from app.ai.contracts import EmbeddingUnavailableError

AI_REQUESTS_PER_MINUTE_ENV = "SERVICEPILOT_AI_REQUESTS_PER_MINUTE"
AI_REQUESTS_PER_DAY_ENV = "SERVICEPILOT_AI_REQUESTS_PER_DAY"
DEFAULT_AI_REQUESTS_PER_MINUTE = 10
DEFAULT_AI_REQUESTS_PER_DAY = 100
MAX_CONFIGURABLE_REQUESTS_PER_MINUTE = 1_000
MAX_CONFIGURABLE_REQUESTS_PER_DAY = 100_000


class AIUsageLimitConfigurationError(ValueError):
    """Segnala limiti assenti o fuori da un intervallo prudente."""


class AIUsageLimitExceeded(EmbeddingUnavailableError):
    """Ferma una chiamata prima che raggiunga il provider esterno."""


@dataclass(frozen=True)
class AIUsageLimitSettings:
    """Soglie globali applicate dal singolo processo della demo."""

    requests_per_minute: int = DEFAULT_AI_REQUESTS_PER_MINUTE
    requests_per_day: int = DEFAULT_AI_REQUESTS_PER_DAY

    def __post_init__(self) -> None:
        if not 1 <= self.requests_per_minute <= MAX_CONFIGURABLE_REQUESTS_PER_MINUTE:
            raise AIUsageLimitConfigurationError(
                f"{AI_REQUESTS_PER_MINUTE_ENV} deve essere compreso tra 1 e "
                f"{MAX_CONFIGURABLE_REQUESTS_PER_MINUTE}"
            )
        if not 1 <= self.requests_per_day <= MAX_CONFIGURABLE_REQUESTS_PER_DAY:
            raise AIUsageLimitConfigurationError(
                f"{AI_REQUESTS_PER_DAY_ENV} deve essere compreso tra 1 e "
                f"{MAX_CONFIGURABLE_REQUESTS_PER_DAY}"
            )
        if self.requests_per_minute > self.requests_per_day:
            raise AIUsageLimitConfigurationError(
                f"{AI_REQUESTS_PER_MINUTE_ENV} non pu\u00f2 superare {AI_REQUESTS_PER_DAY_ENV}"
            )


def _read_limit(
    source: Mapping[str, str],
    variable_name: str,
    default: int,
) -> int:
    raw_value = source.get(variable_name, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError as error:
        raise AIUsageLimitConfigurationError(
            f"{variable_name} deve contenere un numero intero"
        ) from error


def load_ai_usage_limit_settings(
    environment: Mapping[str, str] | None = None,
) -> AIUsageLimitSettings:
    """Legge le soglie dall'ambiente senza dipendere dalla chiave del provider."""

    source = os.environ if environment is None else environment
    return AIUsageLimitSettings(
        requests_per_minute=_read_limit(
            source,
            AI_REQUESTS_PER_MINUTE_ENV,
            DEFAULT_AI_REQUESTS_PER_MINUTE,
        ),
        requests_per_day=_read_limit(
            source,
            AI_REQUESTS_PER_DAY_ENV,
            DEFAULT_AI_REQUESTS_PER_DAY,
        ),
    )


class AIUsageLimiter:
    """Conta in memoria le richieste ammesse e blocca gli eccessi prima della rete."""

    def __init__(
        self,
        settings: AIUsageLimitSettings,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.settings = settings
        self._clock = clock
        self._lock = Lock()
        self._minute_requests: deque[float] = deque()
        self._day: str | None = None
        self._day_requests = 0

    def consume(self) -> None:
        """Prenota una richiesta oppure la rifiuta senza contattare il provider."""

        now = self._clock()
        current_day = datetime.fromtimestamp(now, UTC).date().isoformat()
        with self._lock:
            if self._day != current_day:
                self._day = current_day
                self._day_requests = 0
                self._minute_requests.clear()

            minute_boundary = now - 60
            while self._minute_requests and self._minute_requests[0] <= minute_boundary:
                self._minute_requests.popleft()

            if self._day_requests >= self.settings.requests_per_day:
                raise AIUsageLimitExceeded(
                    "Il limite giornaliero delle chiamate AI della demo \u00e8 stato raggiunto."
                )
            if len(self._minute_requests) >= self.settings.requests_per_minute:
                raise AIUsageLimitExceeded(
                    "Sono state effettuate troppe chiamate AI in un minuto. Riprova pi\u00f9 tardi."
                )

            self._minute_requests.append(now)
            self._day_requests += 1

    @property
    def used_today(self) -> int:
        """Espone il conteggio senza rivelare dati o contenuti delle richieste."""

        with self._lock:
            return self._day_requests


@lru_cache(maxsize=1)
def get_ai_usage_limiter() -> AIUsageLimiter:
    """Condivide un unico contatore tra generazione ed embedding del processo web."""

    return AIUsageLimiter(load_ai_usage_limit_settings())
