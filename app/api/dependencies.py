"""Controlli condivisi per identità autenticata e ruoli autorizzati."""

from collections.abc import Callable
from typing import Annotated, NoReturn

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import AuthSession, User
from app.db.session import get_session
from app.domain.vocabulary import Role
from app.security.sessions import (
    SESSION_COOKIE_NAME,
    hash_session_token,
    session_is_expired,
)

DatabaseSession = Annotated[Session, Depends(get_session)]
SessionCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)]
INVALID_SESSION = "Sessione non valida o scaduta"
FORBIDDEN_ROLE = "Operazione non consentita per il ruolo corrente"


def _reject_invalid_session(
    session: Session,
    auth_session: AuthSession | None,
) -> NoReturn:
    """Rimuove una sessione inutilizzabile e restituisce sempre lo stesso errore."""

    if auth_session is not None:
        session.delete(auth_session)
        session.commit()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_SESSION,
    )


def get_current_user(
    session: DatabaseSession,
    session_token: SessionCookie = None,
) -> User:
    """Restituisce l'utente attivo collegato a una sessione valida."""

    if not session_token:
        _reject_invalid_session(session, None)

    auth_session = session.get(AuthSession, hash_session_token(session_token))
    if auth_session is None or session_is_expired(auth_session.expires_at):
        _reject_invalid_session(session, auth_session)

    user = session.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        _reject_invalid_session(session, auth_session)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: Role) -> Callable[[User], User]:
    """Crea un controllo riutilizzabile che accetta soltanto i ruoli indicati."""

    if not allowed_roles:
        raise ValueError("specificare almeno un ruolo autorizzato")
    allowed = frozenset(allowed_roles)

    def verify_role(current_user: CurrentUser) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=FORBIDDEN_ROLE,
            )
        return current_user

    return verify_role


TechnicalUser = Annotated[
    User,
    Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
]
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
