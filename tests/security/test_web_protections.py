"""Verifiche delle protezioni uniformi per browser e demo pubblica."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.security.configuration import SecurityConfigurationError
from app.security.middleware import LoginAttemptLimiter


def test_public_demo_refuses_insecure_session_cookies(monkeypatch) -> None:
    monkeypatch.setenv("SERVICEPILOT_PUBLIC_DEMO", "true")
    monkeypatch.setenv("SERVICEPILOT_SECURE_COOKIES", "false")

    with pytest.raises(SecurityConfigurationError, match="obbligatorio"):
        create_app(database_initializer=lambda: None)


def test_security_headers_are_added_to_every_response() -> None:
    with TestClient(create_app(database_initializer=lambda: None)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"


def test_cross_site_post_is_rejected_before_reaching_login() -> None:
    with TestClient(create_app(database_initializer=lambda: None)) as client:
        response = client.post(
            "/login",
            data={"email": "demo@example.test", "password": "not-a-real-password"},
            headers={"Origin": "https://attacker.example"},
        )

    assert response.status_code == 403
    assert response.text == "Origine della richiesta non consentita."


def test_malformed_origin_is_rejected_without_an_internal_error() -> None:
    with TestClient(create_app(database_initializer=lambda: None)) as client:
        response = client.post(
            "/login",
            data={"email": "demo@example.test", "password": "not-a-real-password"},
            headers={"Origin": "https://testserver:not-a-port"},
        )

    assert response.status_code == 403


def test_unknown_host_is_rejected() -> None:
    with TestClient(create_app(database_initializer=lambda: None)) as client:
        response = client.get("/health", headers={"Host": "attacker.example"})

    assert response.status_code == 400


def test_https_mode_adds_hsts(monkeypatch) -> None:
    monkeypatch.setenv("SERVICEPILOT_SECURE_COOKIES", "true")

    with TestClient(
        create_app(database_initializer=lambda: None),
        base_url="https://testserver",
    ) as client:
        response = client.get("/health")

    assert response.headers["strict-transport-security"] == "max-age=31536000"


def test_login_attempt_limit_recovers_after_one_minute() -> None:
    current_time = [100.0]
    limiter = LoginAttemptLimiter(2, clock=lambda: current_time[0])

    assert limiter.allow("client-demo") is True
    assert limiter.allow("client-demo") is True
    assert limiter.allow("client-demo") is False
    assert limiter.allow("altro-client-demo") is True

    current_time[0] += 61
    assert limiter.allow("client-demo") is True
