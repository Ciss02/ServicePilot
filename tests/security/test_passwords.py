"""Verifiche dell'hashing delle password."""

import secrets

import pytest

from app.security.passwords import hash_password, verify_password


def test_password_is_stored_as_argon2_hash() -> None:
    password = secrets.token_urlsafe(24)

    encoded_hash = hash_password(password)

    assert encoded_hash.startswith("$argon2id$")
    assert password not in encoded_hash
    assert verify_password(password, encoded_hash)
    assert not verify_password(secrets.token_urlsafe(24), encoded_hash)


def test_same_password_receives_different_random_salts() -> None:
    password = secrets.token_urlsafe(24)

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


@pytest.mark.parametrize("invalid_password", ["", None])
def test_hash_password_rejects_invalid_values(invalid_password: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        hash_password(invalid_password)  # type: ignore[arg-type]


def test_verify_password_rejects_missing_or_unknown_hash() -> None:
    password = secrets.token_urlsafe(24)

    assert not verify_password(password, None)
    assert not verify_password(password, "not-an-encoded-hash")
