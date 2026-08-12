"""Dipendenza FastAPI per il client dei servizi azione simulati."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.actions.service_client import ActionServiceClient, build_action_service_client


@lru_cache(maxsize=1)
def get_action_service_client() -> ActionServiceClient:
    return build_action_service_client()


ActionServiceClientDependency = Annotated[
    ActionServiceClient,
    Depends(get_action_service_client),
]
