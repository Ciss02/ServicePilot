"""Test HTTP di login, sessione autenticata e logout."""

import secrets
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, update
from sqlalchemy.orm import Session

from app.db import AuthSession, User, build_engine, create_database, get_session
from app.domain.vocabulary import Role
from app.main import create_app
from app.security.passwords import hash_password
from app.security.sessions import SESSION_COOKIE_NAME, hash_session_token


@pytest.fixture
def auth_api(tmp_path) -> Iterator[tuple[TestClient, Engine, str]]:
    """Avvia l'app con account fittizi e password casuale in un database isolato."""

    password = secrets.token_urlsafe(18)
    database_engine = build_engine(f"sqlite:///{tmp_path / 'auth-api-test.db'}")

    def initialize_test_database() -> None:
        create_database(database_engine)
        with Session(database_engine) as session:
            if session.scalar(select(func.count()).select_from(User)) == 0:
                session.add_all(
                    [
                        User(
                            email="dipendente@servicepilot.example",
                            display_name="Dipendente Accesso Demo",
                            role=Role.EMPLOYEE,
                            password_hash=hash_password(password),
                        ),
                        User(
                            email="inattivo@servicepilot.example",
                            display_name="Account Inattivo Demo",
                            role=Role.TECHNICIAN,
                            password_hash=hash_password(password),
                            is_active=False,
                        ),
                    ]
                )
                session.commit()

    def override_session() -> Iterator[Session]:
        with Session(database_engine) as session:
            yield session

    test_app = create_app(database_initializer=initialize_test_database)
    test_app.dependency_overrides[get_session] = override_session

    with TestClient(test_app) as client:
        yield client, database_engine, password

    database_engine.dispose()


def login_payload(password: str) -> dict[str, str]:
    return {
        "email": "dipendente@servicepilot.example",
        "password": password,
    }


def test_valid_login_creates_protected_session(auth_api) -> None:
    client, database_engine, password = auth_api

    response = client.post("/auth/login", json=login_payload(password))

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "dipendente@servicepilot.example",
        "display_name": "Dipendente Accesso Demo",
        "role": "employee",
    }
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]

    browser_token = client.cookies.get(SESSION_COOKIE_NAME)
    assert browser_token
    with Session(database_engine) as session:
        stored_session = session.scalar(select(AuthSession))
        assert stored_session is not None
        assert stored_session.token_hash == hash_session_token(browser_token)
        assert stored_session.token_hash != browser_token


def test_session_remembers_authenticated_user(auth_api) -> None:
    client, _, password = auth_api
    client.post("/auth/login", json=login_payload(password))

    response = client.get("/auth/session")

    assert response.status_code == 200
    assert response.json()["email"] == "dipendente@servicepilot.example"
    assert response.json()["role"] == "employee"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "email": "dipendente@servicepilot.example",
            "password": "password-errata-demo",
        },
        {
            "email": "inesistente@servicepilot.example",
            "password": "password-errata-demo",
        },
    ],
    ids=["wrong-password", "unknown-email"],
)
def test_login_rejects_invalid_credentials_with_the_same_error(
    auth_api,
    payload: dict[str, str],
) -> None:
    client, database_engine, _ = auth_api

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == {"detail": "Email o password non validi"}
    assert SESSION_COOKIE_NAME not in client.cookies
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_login_rejects_inactive_account(auth_api) -> None:
    client, _, password = auth_api

    response = client.post(
        "/auth/login",
        json={"email": "inattivo@servicepilot.example", "password": password},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Email o password non validi"}


def test_missing_session_is_rejected(auth_api) -> None:
    client, _, _ = auth_api

    response = client.get("/auth/session")

    assert response.status_code == 401
    assert response.json() == {"detail": "Sessione non valida o scaduta"}


def test_expired_session_is_rejected_and_removed(auth_api) -> None:
    client, database_engine, password = auth_api
    client.post("/auth/login", json=login_payload(password))
    with Session(database_engine) as session:
        session.execute(update(AuthSession).values(expires_at=0))
        session.commit()

    response = client.get("/auth/session")

    assert response.status_code == 401
    assert response.json() == {"detail": "Sessione non valida o scaduta"}
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_session_is_revoked_when_account_becomes_inactive(auth_api) -> None:
    client, database_engine, password = auth_api
    client.post("/auth/login", json=login_payload(password))
    with Session(database_engine) as session:
        user = session.get(User, 1)
        assert user is not None
        user.is_active = False
        session.commit()

    response = client.get("/auth/session")

    assert response.status_code == 401
    assert response.json() == {"detail": "Sessione non valida o scaduta"}
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_logout_revokes_session_and_removes_cookie(auth_api) -> None:
    client, database_engine, password = auth_api
    client.post("/auth/login", json=login_payload(password))

    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    assert SESSION_COOKIE_NAME not in client.cookies
    assert client.get("/auth/session").status_code == 401
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_logout_without_session_is_safe(auth_api) -> None:
    client, _, _ = auth_api

    response = client.post("/auth/logout")

    assert response.status_code == 204
