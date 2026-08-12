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
)
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
    "AIProposedTicketClassification",
    "AIExtractedTicketDetails",
    "AvailableSite",
    "TicketExtractionResult",
    "TicketIntakeField",
    "TicketClassificationPersistenceError",
    "TicketClassificationSuggestion",
    "build_ai_model",
    "classify_confirmed_ticket",
    "extract_ticket_details",
    "load_ai_settings",
    "suggest_ticket_classification",
]
