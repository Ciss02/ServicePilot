"""Configurazione locale per i file della knowledge base."""

import os
from pathlib import Path

KNOWLEDGE_STORAGE_DIRECTORY_ENV = "SERVICEPILOT_KNOWLEDGE_STORAGE_DIR"
DEFAULT_KNOWLEDGE_STORAGE_DIRECTORY = Path("storage") / "knowledge"


def get_knowledge_storage_directory() -> Path:
    """Restituisce la cartella configurata senza esporla nell'interfaccia."""

    configured_path = os.getenv(KNOWLEDGE_STORAGE_DIRECTORY_ENV)
    if configured_path:
        return Path(configured_path).expanduser()
    return DEFAULT_KNOWLEDGE_STORAGE_DIRECTORY
