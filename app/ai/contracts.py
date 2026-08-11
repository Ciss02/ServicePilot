"""Contratto comune che rende il provider AI sostituibile."""

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class AIModelError(RuntimeError):
    """Errore controllato prodotto dal collegamento con un modello AI."""


class AIUnavailableError(AIModelError):
    """Segnala che il provider non è configurato o temporaneamente disponibile."""


class AIProviderError(AIModelError):
    """Nasconde gli errori specifici del provider dietro un errore comune."""


class AIInvalidResponseError(AIModelError):
    """Segnala una risposta che non rispetta la struttura richiesta."""


@runtime_checkable
class AIModel(Protocol):
    """Definisce l'unica operazione AI necessaria alle prossime issue."""

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: type[ResponseModelT],
        system_instruction: str | None = None,
    ) -> ResponseModelT:
        """Genera una risposta e la restituisce già validata dallo schema."""
