"""Adapter Gemini basato sulla libreria ufficiale Google Gen AI."""

from collections.abc import Callable
from typing import Any

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.ai.configuration import AIProvider, AISettings
from app.ai.contracts import (
    AIInvalidResponseError,
    AIProviderError,
    AIUnavailableError,
    ResponseModelT,
)


RETRYABLE_HTTP_STATUS_CODES = [408, 429, 500, 502, 503, 504]


class GeminiAIModel:
    """Traduce il contratto comune nelle chiamate previste da Gemini."""

    def __init__(
        self,
        settings: AISettings,
        client_factory: Callable[..., Any] = genai.Client,
    ) -> None:
        if settings.provider is not AIProvider.GEMINI:
            raise ValueError("GeminiAIModel richiede il provider gemini")
        self._settings = settings
        self._client_factory = client_factory

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[ResponseModelT],
        system_instruction: str | None = None,
    ) -> ResponseModelT:
        """Chiama Gemini e controlla la risposta prima di restituirla."""

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
        generation_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            max_output_tokens=self._settings.max_output_tokens,
        )

        try:
            with self._client_factory(
                api_key=self._settings.api_key,
                http_options=http_options,
            ) as client:
                response = client.models.generate_content(
                    model=self._settings.model,
                    contents=prompt,
                    config=generation_config,
                )
        except (TimeoutError, httpx.TimeoutException) as error:
            raise AIUnavailableError(
                "Il modello AI non ha risposto entro il tempo previsto"
            ) from error
        except errors.APIError as error:
            raise AIProviderError(
                "Il provider AI non ha completato la richiesta"
            ) from error

        return self._validate_response(response, response_schema)

    @staticmethod
    def _validate_response(
        response: Any,
        response_schema: type[ResponseModelT],
    ) -> ResponseModelT:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, response_schema):
            return parsed

        try:
            if parsed is not None:
                return response_schema.model_validate(parsed)
            response_text = getattr(response, "text", None)
            if not isinstance(response_text, str) or not response_text:
                raise ValueError("risposta vuota")
            return response_schema.model_validate_json(response_text)
        except (TypeError, ValueError, ValidationError) as error:
            raise AIInvalidResponseError(
                "Il provider AI ha restituito dati non validi"
            ) from error
