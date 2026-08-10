"""API per accesso, lettura della sessione e logout."""

import os

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DatabaseSession, SessionCookie
from app.db.models import AuthSession, User
from app.domain.auth_contracts import AuthenticatedUser, LoginRequest
from app.security.passwords import verify_password
from app.security.sessions import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_SECONDS,
    generate_session_token,
    hash_session_token,
    session_expiry,
)


router = APIRouter(prefix="/auth", tags=["accesso"])
INVALID_CREDENTIALS = "Email o password non validi"
SECURE_COOKIES_ENV = "SERVICEPILOT_SECURE_COOKIES"


def _secure_cookies_enabled() -> bool:
    """Usa cookie HTTPS quando la configurazione lo richiede."""

    return os.getenv(SECURE_COOKIES_ENV, "false").casefold() == "true"


def _set_session_cookie(response: Response, token: str) -> None:
    """Invia il codice al browser con protezioni adatte a una sessione web."""

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=_secure_cookies_enabled(),
        samesite="lax",
        path="/",
    )


def _delete_session_cookie(response: Response) -> None:
    """Chiede al browser di eliminare il cookie della sessione."""

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=_secure_cookies_enabled(),
        samesite="lax",
        path="/",
    )


@router.post(
    "/login",
    response_model=AuthenticatedUser,
    summary="Accede con un account demo",
)
def login(
    payload: LoginRequest,
    response: Response,
    session: DatabaseSession,
) -> User:
    """Verifica le credenziali e crea una sessione revocabile."""

    user = session.scalar(
        select(User).where(func.lower(User.email) == payload.email)
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )

    token = generate_session_token()
    session.add(
        AuthSession(
            token_hash=hash_session_token(token),
            user_id=user.id,
            expires_at=session_expiry(),
        )
    )
    session.commit()
    _set_session_cookie(response, token)
    return user


@router.get(
    "/session",
    response_model=AuthenticatedUser,
    summary="Legge l'identita autenticata",
)
def read_session(
    current_user: CurrentUser,
) -> User:
    """Riconosce il browser tramite una sessione valida e non scaduta."""

    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Chiude la sessione corrente",
)
def logout(
    response: Response,
    session: DatabaseSession,
    session_token: SessionCookie = None,
) -> None:
    """Revoca la sessione presente e cancella sempre il cookie dal browser."""

    if session_token:
        auth_session = session.get(AuthSession, hash_session_token(session_token))
        if auth_session is not None:
            session.delete(auth_session)
            session.commit()
    _delete_session_cookie(response)
