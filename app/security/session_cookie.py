"""Configurazione condivisa del cookie di sessione."""

from fastapi import Response

from app.security.configuration import load_security_settings
from app.security.sessions import SESSION_COOKIE_NAME, SESSION_DURATION_SECONDS


def secure_cookies_enabled() -> bool:
    """Usa cookie HTTPS quando la configurazione lo richiede."""

    return load_security_settings().secure_cookies


def set_session_cookie(response: Response, token: str) -> None:
    """Invia il codice al browser con protezioni adatte a una sessione web."""

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=secure_cookies_enabled(),
        samesite="lax",
        path="/",
    )


def delete_session_cookie(response: Response) -> None:
    """Chiede al browser di eliminare il cookie della sessione."""

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=secure_cookies_enabled(),
        samesite="lax",
        path="/",
    )
