"""Verifiche dell'adapter Gemini senza effettuare chiamate esterne."""

from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from app.ai.configuration import AIProvider, AISettings
from app.ai.contracts import AIInvalidResponseError, AIModel, AIUnavailableError
from app.ai.factory import DisabledAIModel, build_ai_model
from app.ai.gemini import RETRYABLE_HTTP_STATUS_CODES, GeminiAIModel


class ExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    confidence: float


class FakeAIModel:
    """Sostituto controllato usato dai test delle future funzionalità."""

    def __init__(self, response: ExampleResponse) -> None:
        self.response = response

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[ExampleResponse],
        system_instruction: str | None = None,
    ) -> ExampleResponse:
        del prompt, response_schema, system_instruction
        return self.response


class FakeModels:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response: Any) -> None:
        self.models = FakeModels(response)
        self.closed = False

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.closed = True


class FakeClientFactory:
    def __init__(self, client: FakeClient) -> None:
        self.client = client
        self.kwargs: dict[str, Any] = {}

    def __call__(self, **kwargs: Any) -> FakeClient:
        self.kwargs = kwargs
        return self.client


def gemini_settings() -> AISettings:
    return AISettings(
        provider=AIProvider.GEMINI,
        model="gemini-test-model",
        api_key="test-key-never-sent",
        timeout_seconds=12,
        max_attempts=2,
        max_output_tokens=512,
    )


def test_fake_model_satisfies_the_common_contract() -> None:
    expected = ExampleResponse(category="network", confidence=0.9)
    model: AIModel = FakeAIModel(expected)

    result = model.generate_structured(
        prompt="Problema VPN fittizio",
        response_schema=ExampleResponse,
    )

    assert isinstance(model, AIModel)
    assert result == expected


def test_gemini_adapter_uses_structured_output_and_controlled_limits() -> None:
    expected = ExampleResponse(category="network", confidence=0.9)
    client = FakeClient(SimpleNamespace(parsed=expected, text=None))
    client_factory = FakeClientFactory(client)
    model = GeminiAIModel(gemini_settings(), client_factory=client_factory)

    result = model.generate_structured(
        prompt="Problema VPN fittizio",
        response_schema=ExampleResponse,
        system_instruction="Restituisci soltanto dati controllabili.",
    )

    assert result == expected
    assert client.closed is True
    assert client_factory.kwargs["api_key"] == "test-key-never-sent"
    http_options = client_factory.kwargs["http_options"]
    assert http_options.api_version == "v1"
    assert http_options.timeout == 12_000
    assert http_options.retry_options.attempts == 2
    assert http_options.retry_options.http_status_codes == RETRYABLE_HTTP_STATUS_CODES
    call = client.models.calls[0]
    assert call["model"] == "gemini-test-model"
    assert call["contents"] == "Problema VPN fittizio"
    assert call["config"].response_schema is None
    assert call["config"].response_json_schema == ExampleResponse.model_json_schema()
    assert call["config"].response_json_schema["additionalProperties"] is False
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].max_output_tokens == 512


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(parsed=None, text=None),
        SimpleNamespace(parsed={"category": "network"}, text=None),
        SimpleNamespace(parsed=None, text="not-json"),
    ],
)
def test_gemini_adapter_rejects_invalid_responses(response: Any) -> None:
    client = FakeClient(response)
    model = GeminiAIModel(
        gemini_settings(),
        client_factory=FakeClientFactory(client),
    )

    with pytest.raises(AIInvalidResponseError):
        model.generate_structured(
            prompt="Problema fittizio",
            response_schema=ExampleResponse,
        )


def test_disabled_provider_keeps_the_project_offline() -> None:
    model = build_ai_model(AISettings())

    assert isinstance(model, DisabledAIModel)
    with pytest.raises(AIUnavailableError, match="non è configurato"):
        model.generate_structured(
            prompt="Problema fittizio",
            response_schema=ExampleResponse,
        )


def test_factory_selects_gemini_without_opening_a_connection() -> None:
    model = build_ai_model(gemini_settings())

    assert isinstance(model, GeminiAIModel)
