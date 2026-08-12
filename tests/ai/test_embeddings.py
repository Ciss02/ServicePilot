"""Verifiche dell'adapter embedding senza chiamate esterne."""

from math import isclose, sqrt
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.configuration import AIProvider
from app.ai.contracts import (
    EmbeddingInvalidResponseError,
    EmbeddingModel,
    EmbeddingUnavailableError,
)
from app.ai.embedding_configuration import EmbeddingSettings
from app.ai.embedding_models import (
    DisabledEmbeddingModel,
    GeminiEmbeddingModel,
    build_embedding_model,
)


class FakeModels:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def embed_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[Any]) -> None:
        self.models = FakeModels(responses)
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


def embedding_settings() -> EmbeddingSettings:
    return EmbeddingSettings(
        provider=AIProvider.GEMINI,
        model="gemini-embedding-test",
        dimensions=128,
        api_key="test-key-never-sent",
        timeout_seconds=11,
        max_attempts=2,
    )


def embedding_response(*vectors: list[float]) -> SimpleNamespace:
    return SimpleNamespace(embeddings=[SimpleNamespace(values=vector) for vector in vectors])


def padded_vector(*values: float) -> list[float]:
    return [*values, *([0.0] * (128 - len(values)))]


def test_gemini_embedding_adapter_uses_retrieval_tasks_and_normalizes() -> None:
    client = FakeClient(
        [
            embedding_response(padded_vector(3.0, 4.0), padded_vector(0.0, 2.0)),
            embedding_response(padded_vector(1.0, 1.0)),
        ]
    )
    factory = FakeClientFactory(client)
    model = GeminiEmbeddingModel(embedding_settings(), client_factory=factory)

    documents = model.embed_documents(["Procedura VPN", "Procedura account"])
    query = model.embed_query("La VPN si disconnette")

    assert isinstance(model, EmbeddingModel)
    assert model.model_name == "gemini-embedding-test"
    assert model.dimensions == 128
    assert documents[0][:3] == [0.6, 0.8, 0.0]
    assert documents[1][:3] == [0.0, 1.0, 0.0]
    assert isclose(sum(value * value for value in query), 1.0)
    assert isclose(query[0], 1 / sqrt(2))
    assert client.closed is True
    assert factory.kwargs["api_key"] == "test-key-never-sent"
    http_options = factory.kwargs["http_options"]
    assert http_options.timeout == 11_000
    assert http_options.retry_options.attempts == 2
    document_call, query_call = client.models.calls
    assert document_call["model"] == "gemini-embedding-test"
    assert document_call["config"].task_type == "RETRIEVAL_DOCUMENT"
    assert document_call["config"].output_dimensionality == 128
    assert query_call["config"].task_type == "RETRIEVAL_QUERY"


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(embeddings=None),
        embedding_response([1.0] * 127),
        embedding_response([0.0] * 128),
        embedding_response(padded_vector(float("nan"), 1.0, 2.0)),
    ],
)
def test_embedding_adapter_rejects_invalid_vectors(response: Any) -> None:
    model = GeminiEmbeddingModel(
        embedding_settings(),
        client_factory=FakeClientFactory(FakeClient([response])),
    )

    with pytest.raises(EmbeddingInvalidResponseError):
        model.embed_documents(["Segmento fittizio"])


def test_disabled_embedding_provider_keeps_the_project_offline() -> None:
    model = build_embedding_model(EmbeddingSettings())

    assert isinstance(model, DisabledEmbeddingModel)
    with pytest.raises(EmbeddingUnavailableError, match="non sono configurati"):
        model.embed_query("Domanda fittizia")
