"""Dipendenza FastAPI per usare il modello AI configurato."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.ai.contracts import AIModel, EmbeddingModel
from app.ai.embedding_models import build_embedding_model
from app.ai.factory import build_ai_model
from app.ai.usage_limits import get_ai_usage_limiter


@lru_cache(maxsize=1)
def get_ai_model() -> AIModel:
    """Costruisce una sola istanza dell'adapter configurato per il processo web."""

    return build_ai_model(usage_limiter=get_ai_usage_limiter())


AIModelDependency = Annotated[AIModel, Depends(get_ai_model)]


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """Costruisce una sola istanza dell'adapter embedding per il processo web."""

    return build_embedding_model(usage_limiter=get_ai_usage_limiter())


EmbeddingModelDependency = Annotated[EmbeddingModel, Depends(get_embedding_model)]
