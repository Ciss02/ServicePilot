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


class EmbeddingUnavailableError(AIUnavailableError):
    """Segnala che il provider degli embedding non è configurato o disponibile."""


class EmbeddingProviderError(AIProviderError):
    """Nasconde gli errori specifici del provider degli embedding."""


class EmbeddingInvalidResponseError(AIInvalidResponseError):
    """Segnala vettori mancanti, non numerici o con dimensione errata."""


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


@runtime_checkable
class EmbeddingModel(Protocol):
    """Trasforma documenti e domande nello stesso spazio numerico."""

    @property
    def model_name(self) -> str:
        """Nome stabile salvato insieme all'indice."""

    @property
    def dimensions(self) -> int:
        """Numero atteso di valori per ciascun vettore."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Genera un vettore normalizzato per ciascun segmento."""

    def embed_query(self, text: str) -> list[float]:
        """Genera il vettore normalizzato di una domanda."""
