"""Strumenti di sicurezza condivisi da ServicePilot."""

from app.security.authentication import (
    authenticate_user,
    revoke_user_session,
    start_user_session,
)
from app.security.demo_credentials import (
    DEMO_PASSWORD_ENV_BY_ROLE,
    DemoCredentialsError,
    load_demo_passwords,
    validate_demo_passwords,
)
from app.security.passwords import hash_password, verify_password
from app.security.session_cookie import delete_session_cookie, set_session_cookie
from app.security.sessions import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_SECONDS,
    generate_session_token,
    hash_session_token,
    session_expiry,
    session_is_expired,
)

__all__ = [
    "DEMO_PASSWORD_ENV_BY_ROLE",
    "DemoCredentialsError",
    "SESSION_COOKIE_NAME",
    "SESSION_DURATION_SECONDS",
    "authenticate_user",
    "delete_session_cookie",
    "generate_session_token",
    "hash_password",
    "hash_session_token",
    "load_demo_passwords",
    "revoke_user_session",
    "session_expiry",
    "session_is_expired",
    "set_session_cookie",
    "start_user_session",
    "validate_demo_passwords",
    "verify_password",
]
