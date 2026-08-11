"""Test HTTP del layout, del login web e dell'area protetta."""

import secrets
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.db import AuthSession, User, build_engine, create_database, get_session
from app.domain.vocabulary import Role
from app.main import create_app
from app.security.passwords import hash_password
from app.security.sessions import SESSION_COOKIE_NAME


@pytest.fixture
def web_client(tmp_path) -> Iterator[tuple[TestClient, Engine, str]]:
    """Avvia le pagine con un account fittizio e un database temporaneo."""

    password = secrets.token_urlsafe(18)
    database_engine = build_engine(f"sqlite:///{tmp_path / 'web-pages-test.db'}")

    def initialize_test_database() -> None:
        create_database(database_engine)
        with Session(database_engine) as session:
            if session.scalar(select(func.count()).select_from(User)) == 0:
                session.add(
                    User(
                        email="dipendente.web@servicepilot.example",
                        display_name="Dipendente Web Demo",
                        role=Role.EMPLOYEE,
                        password_hash=hash_password(password),
                    )
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


def test_login_page_has_accessible_responsive_structure(web_client) -> None:
    client, _, _ = web_client

    response = client.get("/login")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert '<html lang="it">' in response.text
    assert 'name="viewport"' in response.text
    assert 'for="email"' in response.text
    assert 'for="password"' in response.text
    assert 'autocomplete="current-password"' in response.text
    assert "Ambiente dimostrativo" in response.text
    assert "Entra in ServicePilot" in response.text


def test_static_styles_define_desktop_and_small_screen_layouts(web_client) -> None:
    client, _, _ = web_client

    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "grid-template-columns" in response.text
    assert "@media (max-width: 860px)" in response.text
    assert "@media (max-width: 620px)" in response.text
    assert "prefers-reduced-motion" in response.text


def test_protected_page_redirects_anonymous_visitor_to_login(web_client) -> None:
    client, _, _ = web_client

    response = client.get("/app", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_invalid_web_login_shows_generic_error_without_password(web_client) -> None:
    client, database_engine, _ = web_client
    wrong_password = secrets.token_urlsafe(18)

    response = client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": wrong_password,
        },
    )

    assert response.status_code == 401
    assert "Accesso non riuscito" in response.text
    assert "Controlla email e password" in response.text
    assert wrong_password not in response.text
    assert SESSION_COOKIE_NAME not in client.cookies
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_valid_web_login_opens_protected_area(web_client) -> None:
    client, database_engine, password = web_client

    response = client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    assert "HttpOnly" in response.headers["set-cookie"]
    assert SESSION_COOKIE_NAME in client.cookies

    protected_page = client.get("/app")
    assert protected_page.status_code == 200
    assert protected_page.headers["cache-control"] == "no-store"
    assert "Buon lavoro, Dipendente Web Demo" in protected_page.text
    assert "Dipendente" in protected_page.text
    assert "Sessione attiva" in protected_page.text
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 1


def test_authenticated_visitor_is_redirected_away_from_login(web_client) -> None:
    client, _, password = web_client
    client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": password,
        },
    )

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/app"


def test_web_logout_revokes_session_and_returns_to_login(web_client) -> None:
    client, database_engine, password = web_client
    client.post(
        "/login",
        data={
            "email": "dipendente.web@servicepilot.example",
            "password": password,
        },
    )

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert SESSION_COOKIE_NAME not in client.cookies
    assert client.get("/app", follow_redirects=False).status_code == 303
    with Session(database_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0
