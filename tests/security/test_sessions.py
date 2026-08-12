"""Test delle funzioni che proteggono i codici di sessione."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import AuthSession, User, build_engine, create_database
from app.domain.vocabulary import Role
from app.security.authentication import start_user_session
from app.security.sessions import (
    SESSION_DURATION_SECONDS,
    generate_session_token,
    hash_session_token,
    session_expiry,
    session_is_expired,
)


def test_generated_session_tokens_are_random_and_not_stored_directly() -> None:
    first_token = generate_session_token()
    second_token = generate_session_token()

    assert first_token != second_token
    assert len(first_token) >= 40
    assert hash_session_token(first_token) != first_token
    assert len(hash_session_token(first_token)) == 64


def test_session_expiry_uses_the_expected_duration() -> None:
    now = 1_800_000_000

    assert session_expiry(now) == now + SESSION_DURATION_SECONDS
    assert not session_is_expired(now + 1, now)
    assert session_is_expired(now, now)


@pytest.mark.parametrize("invalid_token", ["", None, 123])
def test_session_hash_rejects_invalid_tokens(invalid_token) -> None:
    expected_error = ValueError if invalid_token == "" else TypeError

    with pytest.raises(expected_error):
        hash_session_token(invalid_token)


def test_new_login_removes_expired_sessions_and_caps_active_ones(tmp_path) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / 'session-limit-test.db'}")
    create_database(engine)
    now = 1_800_000_000
    with Session(engine) as session:
        user = User(
            email="sessioni.demo@example.test",
            display_name="Utente Sessioni Demo",
            role=Role.EMPLOYEE,
        )
        session.add(user)
        session.flush()
        session.add_all(
            [
                AuthSession(token_hash="a" * 64, user_id=user.id, expires_at=now - 1),
                AuthSession(token_hash="b" * 64, user_id=user.id, expires_at=now + 100),
                AuthSession(token_hash="c" * 64, user_id=user.id, expires_at=now + 200),
            ]
        )
        session.commit()

        token = start_user_session(session, user, now=now, max_active_sessions=2)
        stored_hashes = set(session.scalars(select(AuthSession.token_hash)).all())

        assert session.scalar(select(func.count()).select_from(AuthSession)) == 2
        assert "a" * 64 not in stored_hashes
        assert hash_session_token(token) in stored_hashes

    engine.dispose()
