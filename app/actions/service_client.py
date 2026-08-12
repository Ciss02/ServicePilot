"""Client HTTP controllato per i servizi REST simulati di SP-071."""

import json
import os
import socket
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, uuid5

from pydantic import ValidationError

from app.domain.action_contracts import ActionProposalRead
from app.domain.vocabulary import ActionType
from app.simulated_services.contracts import (
    SimulatedActionFailure,
    SimulatedActionSuccess,
)

ACTION_SERVICE_BASE_URL_ENV = "SERVICEPILOT_ACTION_SERVICE_BASE_URL"
ACTION_SERVICE_TIMEOUT_ENV = "SERVICEPILOT_ACTION_SERVICE_TIMEOUT_SECONDS"
DEFAULT_ACTION_SERVICE_BASE_URL = "http://127.0.0.1:8011"
DEFAULT_ACTION_SERVICE_TIMEOUT_SECONDS = 3.0


class ActionServiceConfigurationError(ValueError):
    """La configurazione del servizio non è sicura o utilizzabile."""


class ActionServiceError(RuntimeError):
    """Il servizio non ha restituito un risultato interpretabile."""


@dataclass(frozen=True)
class ActionServiceSettings:
    base_url: str = DEFAULT_ACTION_SERVICE_BASE_URL
    timeout_seconds: float = DEFAULT_ACTION_SERVICE_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ActionServiceConfigurationError(
                "L'indirizzo dei servizi azione deve essere un URL HTTP valido"
            )
        if parsed.username is not None or parsed.password is not None:
            raise ActionServiceConfigurationError(
                "L'indirizzo dei servizi azione non deve contenere credenziali"
            )
        if not 0 < self.timeout_seconds <= 30:
            raise ActionServiceConfigurationError(
                "Il timeout dei servizi azione deve essere compreso tra 0 e 30 secondi"
            )


@dataclass(frozen=True)
class ActionExecutionResult:
    succeeded: bool
    message: str
    reference: str | None = None
    error_code: str | None = None


class ActionServiceClient:
    """Esegue una proposta tramite una singola chiamata HTTP senza retry."""

    _PATHS = {
        ActionType.ASSIGN_TICKET: "/assignments",
        ActionType.NOTIFY_REQUESTER: "/requester-communications",
        ActionType.ESCALATE_VENDOR: "/vendor-escalations",
    }

    def __init__(self, settings: ActionServiceSettings) -> None:
        self._settings = settings

    def execute(self, proposal: ActionProposalRead) -> ActionExecutionResult:
        request_id = uuid5(
            NAMESPACE_URL,
            f"servicepilot://proposed-actions/{proposal.id}",
        )
        body = json.dumps(
            {
                "request_id": str(request_id),
                "ticket_id": proposal.ticket_id,
                "simulation_scenario": "success",
                "payload": proposal.payload.model_dump(mode="json"),
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            url=(self._settings.base_url.rstrip("/") + self._PATHS[proposal.action_type]),
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self._settings.timeout_seconds) as response:
                raw_response = response.read().decode("utf-8")
            parsed = SimulatedActionSuccess.model_validate_json(raw_response)
            return ActionExecutionResult(
                succeeded=True,
                reference=parsed.reference,
                message=parsed.message,
            )
        except HTTPError as error:
            return self._controlled_http_failure(error)
        except (URLError, TimeoutError, socket.timeout, OSError) as error:
            raise ActionServiceError("Il servizio simulato non è raggiungibile") from error
        except (UnicodeDecodeError, ValidationError) as error:
            raise ActionServiceError(
                "Il servizio simulato ha restituito una risposta non valida"
            ) from error

    @staticmethod
    def _controlled_http_failure(error: HTTPError) -> ActionExecutionResult:
        try:
            failure = SimulatedActionFailure.model_validate_json(error.read().decode("utf-8"))
        except (UnicodeDecodeError, ValidationError) as parse_error:
            raise ActionServiceError(
                "Il servizio simulato ha restituito un errore non valido"
            ) from parse_error
        return ActionExecutionResult(
            succeeded=False,
            error_code=failure.error_code,
            message=failure.message,
        )


def load_action_service_settings() -> ActionServiceSettings:
    """Legge indirizzo e timeout senza includere segreti nel repository."""

    raw_timeout = os.getenv(
        ACTION_SERVICE_TIMEOUT_ENV,
        str(DEFAULT_ACTION_SERVICE_TIMEOUT_SECONDS),
    )
    try:
        timeout = float(raw_timeout)
    except ValueError as error:
        raise ActionServiceConfigurationError(
            "Il timeout dei servizi azione deve essere numerico"
        ) from error
    return ActionServiceSettings(
        base_url=os.getenv(
            ACTION_SERVICE_BASE_URL_ENV,
            DEFAULT_ACTION_SERVICE_BASE_URL,
        ),
        timeout_seconds=timeout,
    )


def build_action_service_client() -> ActionServiceClient:
    return ActionServiceClient(load_action_service_settings())
