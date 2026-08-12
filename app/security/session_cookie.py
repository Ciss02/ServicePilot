"""Configurazione condivisa del cookie di sessione."""

import os

from fastapi import Response

from app.security.sessions import SESSION_COOKIE_NAME, SESSION_DURATION_SECONDS

SECURE_COOKIES_ENV = "SERVICEPILOT_SECURE_COOKIES"


def secure_cookies_enabled() -> bool:
    """Usa cookie HTTPS quando la configurazione lo richiede."""

    return os.getenv(SECURE_COOKIES_ENV, "false").casefold() == "true"


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
