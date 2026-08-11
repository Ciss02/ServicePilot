"""API per accesso, lettura della sessione e logout."""

from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession, SessionCookie
from app.db.models import User
from app.domain.auth_contracts import AuthenticatedUser, LoginRequest
from app.security.authentication import (
    authenticate_user,
    revoke_user_session,
    start_user_session,
)
from app.security.session_cookie import delete_session_cookie, set_session_cookie


router = APIRouter(prefix="/auth", tags=["accesso"])
INVALID_CREDENTIALS = "Email o password non validi"


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

    user = authenticate_user(session, payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )

    token = start_user_session(session, user)
    set_session_cookie(response, token)
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

    revoke_user_session(session, session_token)
    delete_session_cookie(response)
