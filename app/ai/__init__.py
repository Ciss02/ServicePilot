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
from app.ai.usage_limits import (
    AI_REQUESTS_PER_DAY_ENV,
    AI_REQUESTS_PER_MINUTE_ENV,
    AIUsageLimitConfigurationError,
    AIUsageLimiter,
    AIUsageLimitExceeded,
    AIUsageLimitSettings,
    get_ai_usage_limiter,
    load_ai_usage_limit_settings,
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
    "AIUsageLimitConfigurationError",
    "AIUsageLimitExceeded",
    "AIUsageLimitSettings",
    "AIUsageLimiter",
    "AI_REQUESTS_PER_DAY_ENV",
    "AI_REQUESTS_PER_MINUTE_ENV",
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
    "get_ai_usage_limiter",
    "load_ai_settings",
    "load_embedding_settings",
    "load_ai_usage_limit_settings",
    "suggest_ticket_classification",
]
