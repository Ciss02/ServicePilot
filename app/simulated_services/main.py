"""Applicazione REST separata che simula tre integrazioni operative."""

from typing import Protocol
from uuid import UUID

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.domain.vocabulary import ActionType
from app.simulated_services.contracts import (
    SimulatedActionFailure,
    SimulatedActionSuccess,
    SimulatedAssignmentRequest,
    SimulatedRequesterCommunicationRequest,
    SimulatedVendorEscalationRequest,
    SimulationScenario,
)


class _ActionRequest(Protocol):
    request_id: UUID
    ticket_id: int
    simulation_scenario: SimulationScenario


def _simulate_action(
    request: _ActionRequest,
    *,
    action_type: ActionType,
    reference_prefix: str,
    success_message: str,
) -> SimulatedActionSuccess | JSONResponse:
    """Produce un successo o un errore controllato senza effetti esterni."""

    if request.simulation_scenario is SimulationScenario.SERVICE_UNAVAILABLE:
        failure = SimulatedActionFailure(
            request_id=request.request_id,
            ticket_id=request.ticket_id,
            action_type=action_type,
            message="Errore demo: il servizio simulato non è temporaneamente disponibile.",
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=failure.model_dump(mode="json"),
        )

    request_code = str(request.request_id).replace("-", "")[:12].upper()
    return SimulatedActionSuccess(
        request_id=request.request_id,
        ticket_id=request.ticket_id,
        action_type=action_type,
        reference=f"{reference_prefix}-{request_code}",
        message=success_message,
    )


def create_simulated_services_app() -> FastAPI:
    """Costruisce l'app locale, distinta dal portale ServicePilot."""

    application = FastAPI(
        title="ServicePilot - Servizi azione simulati",
        description=(
            "Integrazioni REST fittizie per provare assegnazione, comunicazione "
            "ed escalation senza contattare sistemi reali."
        ),
        version="0.1.0",
    )

    failure_response = {
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": SimulatedActionFailure,
            "description": "Errore intenzionale e ripetibile della simulazione",
        }
    }

    @application.get(
        "/health",
        tags=["sistema simulato"],
        summary="Verifica che i simulatori siano disponibili",
    )
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "simulated-action-services"}

    @application.post(
        "/assignments",
        response_model=SimulatedActionSuccess,
        responses=failure_response,
        tags=["azioni simulate"],
        summary="Simula l'assegnazione di un ticket",
    )
    def simulate_assignment(
        request: SimulatedAssignmentRequest,
    ) -> SimulatedActionSuccess | JSONResponse:
        return _simulate_action(
            request,
            action_type=ActionType.ASSIGN_TICKET,
            reference_prefix="ASG",
            success_message="Assegnazione demo completata senza modificare sistemi reali.",
        )

    @application.post(
        "/requester-communications",
        response_model=SimulatedActionSuccess,
        responses=failure_response,
        tags=["azioni simulate"],
        summary="Simula una comunicazione al richiedente",
    )
    def simulate_requester_communication(
        request: SimulatedRequesterCommunicationRequest,
    ) -> SimulatedActionSuccess | JSONResponse:
        return _simulate_action(
            request,
            action_type=ActionType.NOTIFY_REQUESTER,
            reference_prefix="COM",
            success_message="Comunicazione demo registrata senza inviare messaggi reali.",
        )

    @application.post(
        "/vendor-escalations",
        response_model=SimulatedActionSuccess,
        responses=failure_response,
        tags=["azioni simulate"],
        summary="Simula un'escalation al fornitore",
    )
    def simulate_vendor_escalation(
        request: SimulatedVendorEscalationRequest,
    ) -> SimulatedActionSuccess | JSONResponse:
        return _simulate_action(
            request,
            action_type=ActionType.ESCALATE_VENDOR,
            reference_prefix="ESC",
            success_message="Escalation demo aperta senza contattare fornitori reali.",
        )

    return application


app = create_simulated_services_app()
