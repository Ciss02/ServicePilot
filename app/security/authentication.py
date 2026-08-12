"""Operazioni condivise per autenticare utenti e gestire sessioni."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AuthSession, User
from app.domain.auth_contracts import LoginRequest
from app.security.passwords import verify_password
from app.security.sessions import (
    generate_session_token,
    hash_session_token,
    session_expiry,
)


def authenticate_user(session: Session, credentials: LoginRequest) -> User | None:
    """Restituisce un account attivo quando email e password sono corrette."""

    user = session.scalar(select(User).where(func.lower(User.email) == credentials.email))
    if (
        user is None
        or not user.is_active
        or not verify_password(credentials.password, user.password_hash)
    ):
        return None
    return user


def start_user_session(session: Session, user: User) -> str:
    """Crea e salva una sessione revocabile, restituendo il codice al browser."""

    token = generate_session_token()
    session.add(
        AuthSession(
            token_hash=hash_session_token(token),
            user_id=user.id,
            expires_at=session_expiry(),
        )
    )
    session.commit()
    return token


def revoke_user_session(session: Session, token: str | None) -> None:
    """Elimina la sessione indicata; l'assenza del codice è un caso valido."""

    if not token:
        return
    auth_session = session.get(AuthSession, hash_session_token(token))
    if auth_session is not None:
        session.delete(auth_session)
        session.commit()
