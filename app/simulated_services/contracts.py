"""Contratti HTTP dei servizi di azione completamente simulati."""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.action_contracts import (
    AssignmentActionPayload,
    RequesterCommunicationPayload,
    VendorEscalationPayload,
)
from app.domain.vocabulary import ActionType


Identifier = Annotated[int, Field(strict=True, gt=0)]
ServiceMessage = Annotated[str, Field(min_length=10, max_length=500)]
ServiceReference = Annotated[str, Field(min_length=5, max_length=80)]


class SimulationScenario(StrEnum):
    """Esito scelto esplicitamente per rendere la demo ripetibile."""

    SUCCESS = "success"
    SERVICE_UNAVAILABLE = "service_unavailable"


class SimulatedServiceResult(StrEnum):
    """Esiti che un simulatore può restituire al futuro orchestratore."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class _SimulatedServiceContract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _SimulatedActionRequest(_SimulatedServiceContract):
    request_id: UUID
    ticket_id: Identifier
    simulation_scenario: SimulationScenario = SimulationScenario.SUCCESS


class SimulatedAssignmentRequest(_SimulatedActionRequest):
    payload: AssignmentActionPayload


class SimulatedRequesterCommunicationRequest(_SimulatedActionRequest):
    payload: RequesterCommunicationPayload


class SimulatedVendorEscalationRequest(_SimulatedActionRequest):
    payload: VendorEscalationPayload


class SimulatedActionSuccess(_SimulatedServiceContract):
    request_id: UUID
    ticket_id: Identifier
    action_type: ActionType
    result: Literal[SimulatedServiceResult.SUCCEEDED] = SimulatedServiceResult.SUCCEEDED
    reference: ServiceReference
    message: ServiceMessage


class SimulatedActionFailure(_SimulatedServiceContract):
    request_id: UUID
    ticket_id: Identifier
    action_type: ActionType
    result: Literal[SimulatedServiceResult.FAILED] = SimulatedServiceResult.FAILED
    error_code: Literal["simulated_service_unavailable"] = (
        "simulated_service_unavailable"
    )
    message: ServiceMessage
    retryable: bool = True
