"""Contratti validati per creare, aggiornare e leggere i ticket."""

from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    computed_field,
    field_validator,
    model_validator,
)

from app.domain.priority import calculate_priority
from app.domain.vocabulary import Impact, Priority, TicketCategory, TicketStatus, Urgency


Identifier = Annotated[int, Field(strict=True, gt=0)]
AffectedUsers = Annotated[int, Field(strict=True, ge=1, le=10_000)]
Title = Annotated[str, Field(min_length=5, max_length=120)]
Description = Annotated[str, Field(min_length=10, max_length=4_000)]
ShortText = Annotated[str, Field(min_length=2, max_length=100)]
Note = Annotated[str, Field(min_length=2, max_length=2_000)]


class _ContractModel(BaseModel):
    """Impostazioni comuni ai contratti ricevuti dall'applicazione."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TicketCreate(_ContractModel):
    """Dati confermati necessari per creare un nuovo ticket."""

    title: Title
    description: Description
    requester_id: Identifier
    site_id: Identifier
    service: ShortText
    affected_users: AffectedUsers
    confirmed: StrictBool

    @field_validator("confirmed")
    @classmethod
    def require_confirmation(cls, confirmed: bool) -> bool:
        """Accetta soltanto una conferma booleana esplicita e positiva."""

        if not confirmed:
            raise ValueError("confirmed deve essere true")
        return confirmed


class TicketClassification(_ContractModel):
    """Classificazione completa con priorità calcolata dal backend."""

    category: TicketCategory
    subcategory: ShortText | None = None
    impact: Impact
    urgency: Urgency

    @computed_field(return_type=Priority)
    @property
    def priority(self) -> Priority:
        """Calcola la priorità senza accettarla come dato libero in ingresso."""

        return calculate_priority(self.impact, self.urgency)


class TicketUpdate(_ContractModel):
    """Campi modificabili di un ticket; almeno uno deve essere valorizzato."""

    title: Title | None = None
    description: Description | None = None
    site_id: Identifier | None = None
    service: ShortText | None = None
    affected_users: AffectedUsers | None = None
    status: TicketStatus | None = None
    classification: TicketClassification | None = None
    assigned_group: ShortText | None = None
    assigned_technician_id: Identifier | None = None
    technician_note: Note | None = None
    resolution: Description | None = None

    @model_validator(mode="after")
    def require_at_least_one_value(self) -> Self:
        """Rifiuta richieste che non produrrebbero alcuna modifica."""

        field_names = type(self).model_fields
        if not any(getattr(self, field_name) is not None for field_name in field_names):
            raise ValueError("specificare almeno un campo da aggiornare")
        return self


class TicketRead(_ContractModel):
    """Rappresentazione completa restituita dalle API di lettura."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        str_strip_whitespace=True,
    )

    id: Identifier
    title: Title
    description: Description
    requester_id: Identifier
    site_id: Identifier
    service: ShortText
    affected_users: AffectedUsers
    category: TicketCategory | None
    subcategory: ShortText | None
    impact: Impact | None
    urgency: Urgency | None
    priority: Priority | None
    assigned_group: ShortText | None
    assigned_technician_id: Identifier | None
    status: TicketStatus
    technician_note: Note | None
    resolution: Description | None
    created_at: datetime
    updated_at: datetime
