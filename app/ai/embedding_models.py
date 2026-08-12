"""Adapter sostituibile per gli embedding Gemini della knowledge base."""

from collections.abc import Callable
from math import isfinite, sqrt
from typing import Any

import httpx
from google import genai
from google.genai import errors, types

from app.ai.configuration import AIProvider
from app.ai.contracts import (
    EmbeddingInvalidResponseError,
    EmbeddingModel,
    EmbeddingProviderError,
    EmbeddingUnavailableError,
)
from app.ai.embedding_configuration import EmbeddingSettings, load_embedding_settings
from app.ai.gemini import RETRYABLE_HTTP_STATUS_CODES
from app.ai.usage_limits import AIUsageLimiter, get_ai_usage_limiter


class GeminiEmbeddingModel:
    """Genera vettori confrontabili usando l'API embedding di Gemini."""

    def __init__(
        self,
        settings: EmbeddingSettings,
        client_factory: Callable[..., Any] = genai.Client,
        usage_limiter: AIUsageLimiter | None = None,
    ) -> None:
        if settings.provider is not AIProvider.GEMINI:
            raise ValueError("GeminiEmbeddingModel richiede il provider gemini")
        self._settings = settings
        self._client_factory = client_factory
        self._usage_limiter = usage_limiter

    @property
    def model_name(self) -> str:
        return self._settings.model

    @property
    def dimensions(self) -> int:
        return self._settings.dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError("I segmenti da indicizzare non possono essere vuoti")
        return self._embed(texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("La domanda da cercare non può essere vuota")
        return self._embed([text], task_type="RETRIEVAL_QUERY")[0]

    def _embed(self, texts: list[str], *, task_type: str) -> list[list[float]]:
        http_options = types.HttpOptions(
            api_version="v1",
            timeout=self._settings.timeout_seconds * 1000,
            retry_options=types.HttpRetryOptions(
                attempts=self._settings.max_attempts,
                initial_delay=0.5,
                max_delay=2.0,
                exp_base=2.0,
                jitter=0.25,
                http_status_codes=RETRYABLE_HTTP_STATUS_CODES,
            ),
        )
        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=self.dimensions,
        )
        if self._usage_limiter is not None:
            self._usage_limiter.consume()
        try:
            with self._client_factory(
                api_key=self._settings.api_key,
                http_options=http_options,
            ) as client:
                response = client.models.embed_content(
                    model=self.model_name,
                    contents=texts,
                    config=config,
                )
        except (TimeoutError, httpx.TimeoutException) as error:
            raise EmbeddingUnavailableError(
                "Il modello di ricerca non ha risposto entro il tempo previsto"
            ) from error
        except errors.APIError as error:
            raise EmbeddingProviderError(
                "Il provider non ha generato l'indice della knowledge base"
            ) from error

        return self._validate_response(response, expected_count=len(texts))

    def _validate_response(
        self,
        response: Any,
        *,
        expected_count: int,
    ) -> list[list[float]]:
        embeddings = getattr(response, "embeddings", None)
        if not isinstance(embeddings, list) or len(embeddings) != expected_count:
            raise EmbeddingInvalidResponseError(
                "Il provider ha restituito un numero inatteso di vettori"
            )

        normalized_vectors: list[list[float]] = []
        for embedding in embeddings:
            raw_values = getattr(embedding, "values", None)
            if not isinstance(raw_values, list) or len(raw_values) != self.dimensions:
                raise EmbeddingInvalidResponseError(
                    "Il provider ha restituito un vettore con dimensione inattesa"
                )
            try:
                vector = [float(value) for value in raw_values]
            except (TypeError, ValueError) as error:
                raise EmbeddingInvalidResponseError(
                    "Il provider ha restituito valori non numerici"
                ) from error
            if not all(isfinite(value) for value in vector):
                raise EmbeddingInvalidResponseError(
                    "Il provider ha restituito valori numerici non validi"
                )
            norm = sqrt(sum(value * value for value in vector))
            if norm == 0:
                raise EmbeddingInvalidResponseError(
                    "Il provider ha restituito un vettore privo di informazioni"
                )
            normalized_vectors.append([value / norm for value in vector])
        return normalized_vectors


class DisabledEmbeddingModel:
    """Mantiene upload e test disponibili quando gli embedding sono disattivati."""

    def __init__(self, settings: EmbeddingSettings) -> None:
        self._settings = settings

    @property
    def model_name(self) -> str:
        return self._settings.model

    @property
    def dimensions(self) -> int:
        return self._settings.dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        del texts
        raise EmbeddingUnavailableError("Gli embedding non sono configurati")

    def embed_query(self, text: str) -> list[float]:
        del text
        raise EmbeddingUnavailableError("Gli embedding non sono configurati")


def build_embedding_model(
    settings: EmbeddingSettings | None = None,
    *,
    usage_limiter: AIUsageLimiter | None = None,
) -> EmbeddingModel:
    """Restituisce il provider configurato dietro il contratto comune."""

    configured = settings or load_embedding_settings()
    if configured.provider is AIProvider.GEMINI:
        return GeminiEmbeddingModel(
            configured,
            usage_limiter=usage_limiter or get_ai_usage_limiter(),
        )
    return DisabledEmbeddingModel(configured)
