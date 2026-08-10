"""Creazione e protezione dei codici di sessione."""

import hashlib
import secrets
import time


SESSION_COOKIE_NAME = "servicepilot_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60


def generate_session_token() -> str:
    """Crea un codice casuale sufficientemente lungo per una nuova sessione."""

    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Trasforma il codice prima di conservarlo nel database."""

    if not isinstance(token, str):
        raise TypeError("token deve essere una stringa")
    if not token:
        raise ValueError("token non puo essere vuoto")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiry(now: int | None = None) -> int:
    """Calcola la scadenza Unix della sessione, otto ore dopo la creazione."""

    current_time = int(time.time()) if now is None else now
    return current_time + SESSION_DURATION_SECONDS


def session_is_expired(expires_at: int, now: int | None = None) -> bool:
    """Indica se la scadenza e stata raggiunta o superata."""

    current_time = int(time.time()) if now is None else now
    return expires_at <= current_time
