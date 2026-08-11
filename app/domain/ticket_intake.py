"""Contratti per la raccolta guidata prima della conferma del ticket."""

from pydantic import BaseModel, ConfigDict

from app.domain.ticket_contracts import (
    AffectedUsers,
    Description,
    Identifier,
    ShortText,
    Title,
)


class _IntakeModel(BaseModel):
    """Applica le stesse regole di pulizia a ogni passaggio del percorso."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TicketProblemInput(_IntakeModel):
    """Prima risposta libera del dipendente."""

    description: Description


class TicketMissingDetailsInput(_IntakeModel):
    """Dati essenziali che non si possono ricavare dalla sola descrizione."""

    title: Title
    site_id: Identifier
    service: ShortText
    affected_users: AffectedUsers
