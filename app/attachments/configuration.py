"""Configurazione della cartella privata degli allegati."""

import os
from pathlib import Path

ATTACHMENT_STORAGE_DIRECTORY_ENV = "SERVICEPILOT_ATTACHMENT_STORAGE_DIR"
DEFAULT_ATTACHMENT_STORAGE_DIRECTORY = Path("storage") / "attachments"


def get_attachment_storage_directory() -> Path:
    """Restituisce lo storage locale senza esporne il percorso ai client."""

    configured_path = os.getenv(ATTACHMENT_STORAGE_DIRECTORY_ENV)
    if configured_path:
        return Path(configured_path).expanduser()
    return DEFAULT_ATTACHMENT_STORAGE_DIRECTORY
