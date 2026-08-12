"""Verifiche dei tetti locali applicati prima delle chiamate AI reali."""

import pytest
from pydantic import BaseModel

from app.ai.configuration import AIProvider, AISettings
from app.ai.embedding_configuration import EmbeddingSettings
from app.ai.embedding_models import GeminiEmbeddingModel
from app.ai.gemini import GeminiAIModel
from app.ai.usage_limits import (
    AIUsageLimitConfigurationError,
    AIUsageLimiter,
    AIUsageLimitExceeded,
    AIUsageLimitSettings,
    load_ai_usage_limit_settings,
)


class ExampleResponse(BaseModel):
    value: str


class ClientFactoryThatMustNotRun:
    def __call__(self, **_kwargs):
        raise AssertionError("Il client esterno non deve essere costruito oltre la quota")


def test_limits_are_loaded_with_prudent_defaults_and_validated() -> None:
    settings = load_ai_usage_limit_settings({})

    assert settings.requests_per_minute == 10
    assert settings.requests_per_day == 100

    with pytest.raises(AIUsageLimitConfigurationError, match="non pu\u00f2 superare"):
        load_ai_usage_limit_settings(
            {
                "SERVICEPILOT_AI_REQUESTS_PER_MINUTE": "20",
                "SERVICEPILOT_AI_REQUESTS_PER_DAY": "10",
            }
        )


def test_minute_limit_recovers_after_the_window() -> None:
    current_time = [1_800_000_000.0]
    limiter = AIUsageLimiter(
        AIUsageLimitSettings(requests_per_minute=2, requests_per_day=3),
        clock=lambda: current_time[0],
    )

    limiter.consume()
    limiter.consume()
    with pytest.raises(AIUsageLimitExceeded, match="un minuto"):
        limiter.consume()

    current_time[0] += 61
    limiter.consume()
    assert limiter.used_today == 3


def test_day_limit_resets_on_the_next_utc_day() -> None:
    current_time = [1_800_000_000.0]
    limiter = AIUsageLimiter(
        AIUsageLimitSettings(requests_per_minute=2, requests_per_day=2),
        clock=lambda: current_time[0],
    )

    limiter.consume()
    current_time[0] += 61
    limiter.consume()
    with pytest.raises(AIUsageLimitExceeded, match="giornaliero"):
        limiter.consume()

    current_time[0] += 24 * 60 * 60
    limiter.consume()
    assert limiter.used_today == 1


def test_generation_and_embeddings_are_blocked_before_opening_a_client() -> None:
    limiter = AIUsageLimiter(
        AIUsageLimitSettings(requests_per_minute=2, requests_per_day=2),
        clock=lambda: 1_800_000_000.0,
    )
    limiter.consume()
    limiter.consume()
    ai_model = GeminiAIModel(
        AISettings(provider=AIProvider.GEMINI, api_key="fake-test-key"),
        client_factory=ClientFactoryThatMustNotRun(),
        usage_limiter=limiter,
    )
    embedding_model = GeminiEmbeddingModel(
        EmbeddingSettings(
            provider=AIProvider.GEMINI,
            dimensions=128,
            api_key="fake-test-key",
        ),
        client_factory=ClientFactoryThatMustNotRun(),
        usage_limiter=limiter,
    )

    with pytest.raises(AIUsageLimitExceeded):
        ai_model.generate_structured(
            prompt="Richiesta fittizia",
            response_schema=ExampleResponse,
        )
    with pytest.raises(AIUsageLimitExceeded):
        embedding_model.embed_query("Domanda fittizia")
