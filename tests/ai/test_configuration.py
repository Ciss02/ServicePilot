"""Verifiche della configurazione esterna dell'AI."""

import pytest

from app.ai.configuration import (
    AI_MAX_ATTEMPTS_ENV,
    AI_MODEL_ENV,
    AI_PROVIDER_ENV,
    AI_TIMEOUT_ENV,
    DEFAULT_AI_MODEL,
    GEMINI_API_KEY_ENV,
    AIConfigurationError,
    AIProvider,
    load_ai_settings,
)


def test_ai_is_disabled_by_default_without_requiring_a_key() -> None:
    settings = load_ai_settings({})

    assert settings.provider is AIProvider.DISABLED
    assert settings.model == DEFAULT_AI_MODEL
    assert settings.api_key is None


def test_gemini_settings_are_loaded_without_exposing_the_key() -> None:
    secret_key = "gemini-test-key-never-log"
    settings = load_ai_settings(
        {
            AI_PROVIDER_ENV: "GeMiNi",
            GEMINI_API_KEY_ENV: secret_key,
            AI_MODEL_ENV: "gemini-test-model",
            AI_TIMEOUT_ENV: "20",
            AI_MAX_ATTEMPTS_ENV: "3",
        }
    )

    assert settings.provider is AIProvider.GEMINI
    assert settings.api_key == secret_key
    assert settings.model == "gemini-test-model"
    assert settings.timeout_seconds == 20
    assert settings.max_attempts == 3
    assert secret_key not in repr(settings)


def test_gemini_requires_a_key_without_exposing_other_values() -> None:
    environment = {
        AI_PROVIDER_ENV: "gemini",
        AI_MODEL_ENV: "private-model-name",
    }

    with pytest.raises(AIConfigurationError) as error:
        load_ai_settings(environment)

    assert GEMINI_API_KEY_ENV in str(error.value)
    assert environment[AI_MODEL_ENV] not in str(error.value)


@pytest.mark.parametrize(
    ("variable_name", "value"),
    [
        (AI_TIMEOUT_ENV, "0"),
        (AI_TIMEOUT_ENV, "not-a-number"),
        (AI_MAX_ATTEMPTS_ENV, "4"),
    ],
)
def test_unsafe_numeric_ai_settings_are_rejected(
    variable_name: str,
    value: str,
) -> None:
    with pytest.raises(AIConfigurationError, match=variable_name):
        load_ai_settings({variable_name: value})


def test_unknown_ai_provider_is_rejected() -> None:
    with pytest.raises(AIConfigurationError, match=AI_PROVIDER_ENV):
        load_ai_settings({AI_PROVIDER_ENV: "unknown-provider"})
