"""Creazione e verifica degli hash delle password."""

from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError


_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Trasforma una password non vuota usando l'algoritmo raccomandato Argon2."""

    if not isinstance(password, str):
        raise TypeError("password deve essere una stringa")
    if not password:
        raise ValueError("password non può essere vuota")
    return _password_hash.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    """Confronta una password con un hash senza errori per hash non validi."""

    if not isinstance(password, str) or not password or not encoded_hash:
        return False
    try:
        return _password_hash.verify(password, encoded_hash)
    except PwdlibError:
        return False
