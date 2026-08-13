"""Contratti controllati per le azioni proposte dall'agente."""

from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.vocabulary import ActionStatus, ActionType

Identifier = Annotated[int, Field(strict=True, gt=0)]
Rationale = Annotated[str, Field(min_length=20, max_length=1_000)]
ExpectedEffect = Annotated[str, Field(min_length=10, max_length=1_000)]
Message = Annotated[str, Field(min_length=5, max_length=2_000)]
VendorName = Annotated[str, Field(min_length=2, max_length=120)]
EscalationSummary = Annotated[str, Field(min_length=10, max_length=2_000)]
ExecutionReference = Annotated[str, Field(min_length=5, max_length=80)]
ExecutionMessage = Annotated[str, Field(min_length=10, max_length=500)]
ExecutionErrorCode = Annotated[str, Field(min_length=3, max_length=100)]
AssignmentGroupName = Annotated[str, Field(min_length=2, max_length=100)]


class _ActionContract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AssignmentActionPayload(_ActionContract):
    """Destinazione proposta; almeno gruppo o tecnico deve essere presente."""

    assigned_group: AssignmentGroupName | None = None
    assigned_technician_id: Identifier | None = None

    @model_validator(mode="after")
    def require_destination(self) -> Self:
        if self.assigned_group is None and self.assigned_technician_id is None:
            raise ValueError("specificare un gruppo o un tecnico")
        return self


class RequesterCommunicationPayload(_ActionContract):
    """Messaggio che sarà inviato al richiedente soltanto dopo approvazione."""

    message: Message


class VendorEscalationPayload(_ActionContract):
    """Dati fittizi necessari alla futura escalation simulata."""

    vendor_name: VendorName
    summary: EscalationSummary


ActionPayload = AssignmentActionPayload | RequesterCommunicationPayload | VendorEscalationPayload


class ActionProposalCreate(_ActionContract):
    """Proposta validata prima del salvataggio; non contiene comandi di esecuzione."""

    action_type: ActionType
    rationale: Rationale
    payload: ActionPayload
    expected_effect: ExpectedEffect

    @model_validator(mode="after")
    def require_matching_payload(self) -> Self:
        expected_payload = {
            ActionType.ASSIGN_TICKET: AssignmentActionPayload,
            ActionType.NOTIFY_REQUESTER: RequesterCommunicationPayload,
            ActionType.ESCALATE_VENDOR: VendorEscalationPayload,
        }[self.action_type]
        if not isinstance(self.payload, expected_payload):
            raise ValueError("i dati non corrispondono al tipo di azione")
        return self


class ActionProposalRead(ActionProposalCreate):
    """Proposta ricaricata dal database con stato e riferimenti persistenti."""

    id: Identifier
    ticket_id: Identifier
    status: ActionStatus
    reviewed_by_user_id: Identifier | None = None
    decided_at: datetime | None = None
    execution_reference: ExecutionReference | None = None
    execution_message: ExecutionMessage | None = None
    execution_error_code: ExecutionErrorCode | None = None
    created_at: datetime
    updated_at: datetime
