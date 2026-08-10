"""API per accesso, lettura della sessione e logout."""

import os
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AuthSession, User
from app.db.session import get_session
from app.domain.auth_contracts import AuthenticatedUser, LoginRequest
from app.security.passwords import verify_password
from app.security.sessions import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_SECONDS,
    generate_session_token,
    hash_session_token,
    session_expiry,
    session_is_expired,
)


router = APIRouter(prefix="/auth", tags=["accesso"])
DatabaseSession = Annotated[Session, Depends(get_session)]
SessionCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)]
INVALID_CREDENTIALS = "Email o password non validi"
INVALID_SESSION = "Sessione non valida o scaduta"
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


def _reject_invalid_session(session: Session, auth_session: AuthSession | None) -> None:
    """Rimuove una sessione inutilizzabile prima di restituire un errore uniforme."""

    if auth_session is not None:
        session.delete(auth_session)
        session.commit()
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_SESSION)


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
    session: DatabaseSession,
    session_token: SessionCookie = None,
) -> User:
    """Riconosce il browser tramite una sessione valida e non scaduta."""

    if not session_token:
        _reject_invalid_session(session, None)

    auth_session = session.get(AuthSession, hash_session_token(session_token))
    if auth_session is None or session_is_expired(auth_session.expires_at):
        _reject_invalid_session(session, auth_session)

    user = session.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        _reject_invalid_session(session, auth_session)
    return user


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
