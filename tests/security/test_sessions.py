"""Test delle funzioni che proteggono i codici di sessione."""

import pytest

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
