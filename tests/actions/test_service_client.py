"""Verifica la chiamata HTTP e la configurazione del client dei simulatori."""

import io
import json
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError

import pytest

from app.actions import (
    ActionServiceClient,
    ActionServiceConfigurationError,
    ActionServiceError,
    ActionServiceSettings,
    load_action_service_settings,
)
from app.domain import (
    ActionProposalRead,
    ActionStatus,
    ActionType,
    RequesterCommunicationPayload,
)


class HTTPResponseStub:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _proposal() -> ActionProposalRead:
    now = datetime.now(UTC)
    return ActionProposalRead(
        id=12,
        ticket_id=7,
        action_type=ActionType.NOTIFY_REQUESTER,
        rationale="Il richiedente attende una comunicazione demo controllata.",
        payload=RequesterCommunicationPayload(
            message="La verifica demo è in corso e seguirà un aggiornamento."
        ),
        expected_effect="Registrare una comunicazione completamente fittizia.",
        status=ActionStatus.PENDING_APPROVAL,
        created_at=now,
        updated_at=now,
    )


def test_client_posts_validated_payload_and_reads_success(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return HTTPResponseStub(
            {
                "request_id": captured["body"]["request_id"],
                "ticket_id": 7,
                "action_type": "notify_requester",
                "result": "succeeded",
                "reference": "COM-HTTP-DEMO",
                "message": "Comunicazione demo registrata senza inviare messaggi reali.",
            }
        )

    monkeypatch.setattr("app.actions.service_client.urlopen", fake_urlopen)
    client = ActionServiceClient(
        ActionServiceSettings(base_url="http://127.0.0.1:9011", timeout_seconds=2)
    )

    result = client.execute(_proposal())

    assert result.succeeded is True
    assert result.reference == "COM-HTTP-DEMO"
    assert captured["url"] == "http://127.0.0.1:9011/requester-communications"
    assert captured["timeout"] == 2
    assert captured["body"]["ticket_id"] == 7
    assert captured["body"]["simulation_scenario"] == "success"
    assert captured["body"]["payload"] == {
        "message": "La verifica demo è in corso e seguirà un aggiornamento."
    }


def test_client_reads_structured_simulated_failure(monkeypatch) -> None:
    body = json.dumps(
        {
            "request_id": "2ae872a2-98eb-5108-9f82-ea1944758b54",
            "ticket_id": 7,
            "action_type": "notify_requester",
            "result": "failed",
            "error_code": "simulated_service_unavailable",
            "message": "Errore demo: servizio simulato temporaneamente non disponibile.",
            "retryable": True,
        }
    ).encode("utf-8")

    def fake_urlopen(_request, timeout):
        del timeout
        raise HTTPError(
            url="http://127.0.0.1:9011/requester-communications",
            code=503,
            msg="demo",
            hdrs=None,
            fp=io.BytesIO(body),
        )

    monkeypatch.setattr("app.actions.service_client.urlopen", fake_urlopen)
    client = ActionServiceClient(ActionServiceSettings())

    result = client.execute(_proposal())

    assert result.succeeded is False
    assert result.error_code == "simulated_service_unavailable"
    assert "Errore demo" in result.message


def test_network_failure_is_reported_without_retry(monkeypatch) -> None:
    calls = 0

    def fake_urlopen(_request, timeout):
        nonlocal calls
        del timeout
        calls += 1
        raise URLError("simulatore spento")

    monkeypatch.setattr("app.actions.service_client.urlopen", fake_urlopen)

    with pytest.raises(ActionServiceError):
        ActionServiceClient(ActionServiceSettings()).execute(_proposal())
    assert calls == 1


@pytest.mark.parametrize(
    "base_url",
    ["not-an-url", "file:///tmp/demo", "http://user:secret@localhost:8011"],
)
def test_configuration_rejects_unsafe_or_invalid_urls(base_url: str) -> None:
    with pytest.raises(ActionServiceConfigurationError):
        ActionServiceSettings(base_url=base_url)


def test_settings_are_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "SERVICEPILOT_ACTION_SERVICE_BASE_URL",
        "http://127.0.0.1:8123",
    )
    monkeypatch.setenv("SERVICEPILOT_ACTION_SERVICE_TIMEOUT_SECONDS", "4.5")

    settings = load_action_service_settings()

    assert settings.base_url == "http://127.0.0.1:8123"
    assert settings.timeout_seconds == 4.5
