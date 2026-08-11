"""Dipendenza FastAPI per usare il modello AI configurato."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.ai.contracts import AIModel
from app.ai.factory import build_ai_model


@lru_cache(maxsize=1)
def get_ai_model() -> AIModel:
    """Costruisce una sola istanza dell'adapter configurato per il processo web."""

    return build_ai_model()


AIModelDependency = Annotated[AIModel, Depends(get_ai_model)]
