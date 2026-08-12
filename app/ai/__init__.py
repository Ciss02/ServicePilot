"""Collegamento sostituibile tra ServicePilot e i modelli AI."""

from app.ai.configuration import (
    AIConfigurationError,
    AIProvider,
    AISettings,
    load_ai_settings,
)
from app.ai.contracts import (
    AIInvalidResponseError,
    AIModel,
    AIModelError,
    AIProviderError,
    AIUnavailableError,
    EmbeddingInvalidResponseError,
    EmbeddingModel,
    EmbeddingProviderError,
    EmbeddingUnavailableError,
)
from app.ai.embedding_configuration import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS_ENV,
    EMBEDDING_MODEL_ENV,
    EMBEDDING_PROVIDER_ENV,
    EmbeddingSettings,
    load_embedding_settings,
)
from app.ai.embedding_models import build_embedding_model
from app.ai.factory import build_ai_model
from app.ai.ticket_classification import (
    AIProposedTicketClassification,
    TicketClassificationPersistenceError,
    TicketClassificationSuggestion,
    classify_confirmed_ticket,
    suggest_ticket_classification,
)
from app.ai.ticket_extraction import (
    AIExtractedTicketDetails,
    AvailableSite,
    TicketExtractionResult,
    TicketIntakeField,
    extract_ticket_details,
)

__all__ = [
    "AIInvalidResponseError",
    "AIConfigurationError",
    "AIModel",
    "AIModelError",
    "AIProvider",
    "AIProviderError",
    "AISettings",
    "AIUnavailableError",
    "DEFAULT_EMBEDDING_DIMENSIONS",
    "DEFAULT_EMBEDDING_MODEL",
    "EMBEDDING_DIMENSIONS_ENV",
    "EMBEDDING_MODEL_ENV",
    "EMBEDDING_PROVIDER_ENV",
    "EmbeddingInvalidResponseError",
    "EmbeddingModel",
    "EmbeddingProviderError",
    "EmbeddingSettings",
    "EmbeddingUnavailableError",
    "AIProposedTicketClassification",
    "AIExtractedTicketDetails",
    "AvailableSite",
    "TicketExtractionResult",
    "TicketIntakeField",
    "TicketClassificationPersistenceError",
    "TicketClassificationSuggestion",
    "build_ai_model",
    "build_embedding_model",
    "classify_confirmed_ticket",
    "extract_ticket_details",
    "load_ai_settings",
    "load_embedding_settings",
    "suggest_ticket_classification",
]
