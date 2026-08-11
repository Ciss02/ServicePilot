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

__all__ = [
    "AIInvalidResponseError",
    "AIConfigurationError",
    "AIModel",
    "AIModelError",
    "AIProvider",
    "AIProviderError",
    "AISettings",
    "AIUnavailableError",
    "build_ai_model",
    "load_ai_settings",
]
