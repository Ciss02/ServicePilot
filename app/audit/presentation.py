"""Presentazione leggibile degli eventi senza esporre il JSON interno."""

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, Ticket, User
from app.domain.vocabulary import AuditActorType, AuditEventType


EVENT_TYPE_LABELS = {
    AuditEventType.TICKET_CREATED: "Creazione",
    AuditEventType.TICKET_UPDATED: "Aggiornamento",
    AuditEventType.TICKET_STATUS_CHANGED: "Stato",
    AuditEventType.TICKET_ASSIGNMENT_CHANGED: "Assegnazione",
    AuditEventType.AI_CLASSIFICATION_SUGGESTED: "Classificazione AI",
    AuditEventType.AI_CLASSIFICATION_UNAVAILABLE: "Classificazione AI",
    AuditEventType.AI_CLASSIFICATION_INVALID: "Classificazione AI",
    AuditEventType.CLASSIFICATION_REVIEWED: "Revisione umana",
    AuditEventType.AI_SOLUTION_GENERATED: "Soluzione AI",
    AuditEventType.AI_SOLUTION_UNAVAILABLE: "Soluzione AI",
    AuditEventType.AI_SOLUTION_INVALID: "Soluzione AI",
    AuditEventType.ACTION_PROPOSED: "Azione proposta",
    AuditEventType.ACTION_APPROVED: "Approvazione",
    AuditEventType.ACTION_REJECTED: "Rifiuto",
    AuditEventType.ACTION_EXECUTION_STARTED: "Esecuzione",
    AuditEventType.ACTION_EXECUTION_SUCCEEDED: "Esito",
    AuditEventType.ACTION_EXECUTION_FAILED: "Esito",
}
DETAIL_LABELS = {
    "status": "Stato iniziale",
    "from_status": "Stato precedente",
    "to_status": "Nuovo stato",
    "category": "Categoria",
    "impact": "Impatto",
    "urgency": "Urgenza",
    "priority": "Priorità",
    "assigned_group": "Gruppo suggerito",
    "from_group": "Gruppo precedente",
    "to_group": "Nuovo gruppo",
    "from_technician_id": "Tecnico precedente",
    "to_technician_id": "Nuovo tecnico",
    "changed_fields": "Campi aggiornati",
    "result": "Risultato",
    "source_count": "Fonti utilizzate",
    "action_type": "Tipo di azione",
    "decision": "Decisione",
    "reference": "Riferimento simulato",
    "error_code": "Codice errore",
}
VALUE_LABELS = {
    "new": "Nuovo",
    "in_progress": "In lavorazione",
    "waiting_for_requester": "In attesa del richiedente",
    "waiting_for_vendor": "In attesa del fornitore",
    "resolved": "Risolto",
    "closed": "Chiuso",
    "approve": "Approvata",
    "reject": "Rifiutata",
    "assign_ticket": "Assegnazione ticket",
    "notify_requester": "Comunicazione al richiedente",
    "escalate_vendor": "Escalation al fornitore",
    "generated": "Generato",
    "unavailable": "Non disponibile",
    "invalid_response": "Risposta non valida",
    "low": "Basso",
    "medium": "Medio",
    "high": "Alto",
    "account_and_access": "Account e accessi",
    "devices_and_hardware": "Dispositivi e hardware",
    "software_and_applications": "Software e applicazioni",
    "network_and_connectivity": "Rete e connettività",
    "printers_and_labeling": "Stampanti ed etichettatura",
    "telephony": "Telefonia",
    "retail_systems": "Sistemi di negozio",
    "production_systems": "Sistemi produttivi",
    "information_security": "Sicurezza informatica",
    "other_requests": "Altre richieste",
    "p1": "P1 · Critica",
    "p2": "P2 · Alta",
    "p3": "P3 · Media",
    "p4": "P4 · Bassa",
}
FIELD_LABELS = {
    "classification": "classificazione",
    "site": "sede",
    "service": "servizio",
    "affected_users": "persone coinvolte",
    "technician_note": "nota tecnica",
    "resolution": "soluzione finale",
}


@dataclass(frozen=True)
class AuditDetailItem:
    label: str
    value: str


@dataclass(frozen=True)
class AuditEventView:
    id: int
    ticket_id: int
    ticket_code: str
    ticket_title: str
    actor_name: str
    actor_label: str
    actor_class: str
    event_label: str
    summary: str
    detail_items: tuple[AuditDetailItem, ...]
    created_date: str
    created_time: str


def _display_value(key: str, value: object, users: dict[int, User]) -> str:
    if value is None or value == "":
        return "Non assegnato"
    if key in {"from_technician_id", "to_technician_id"}:
        user = users.get(int(value))
        return user.display_name if user else "Tecnico non disponibile"
    if key == "changed_fields" and isinstance(value, list):
        return ", ".join(FIELD_LABELS.get(str(item), str(item)) for item in value)
    if key in {"reference", "error_code"}:
        return str(value)
    if isinstance(value, bool):
        return "Sì" if value else "No"
    return VALUE_LABELS.get(str(value), str(value).replace("_", " ").capitalize())


def present_audit_events(
    session: Session,
    events: list[AuditEvent],
) -> list[AuditEventView]:
    user_ids = {
        identifier
        for event in events
        for identifier in (event.actor_user_id,)
        if identifier is not None
    }
    for event in events:
        try:
            details = json.loads(event.details_json)
        except (json.JSONDecodeError, TypeError):
            continue
        for key in ("from_technician_id", "to_technician_id"):
            identifier = details.get(key)
            if isinstance(identifier, int):
                user_ids.add(identifier)
    users = (
        session.scalars(select(User).where(User.id.in_(user_ids))).all()
        if user_ids
        else []
    )
    users_by_id = {user.id: user for user in users}
    ticket_ids = {event.ticket_id for event in events}
    tickets = (
        session.scalars(select(Ticket).where(Ticket.id.in_(ticket_ids))).all()
        if ticket_ids
        else []
    )
    tickets_by_id = {ticket.id: ticket for ticket in tickets}

    views: list[AuditEventView] = []
    for event in events:
        try:
            raw_details = json.loads(event.details_json)
            details = raw_details if isinstance(raw_details, dict) else {}
        except (json.JSONDecodeError, TypeError):
            details = {}
        actor = users_by_id.get(event.actor_user_id) if event.actor_user_id else None
        if event.actor_type is AuditActorType.HUMAN:
            actor_name = actor.display_name if actor else "Utente non disponibile"
            actor_label = "Persona"
        elif event.actor_type is AuditActorType.AI:
            actor_name = "Assistente AI"
            actor_label = "Intelligenza artificiale"
        else:
            actor_name = "ServicePilot"
            actor_label = "Sistema"
        ticket = tickets_by_id.get(event.ticket_id)
        views.append(
            AuditEventView(
                id=event.id,
                ticket_id=event.ticket_id,
                ticket_code=f"SP-{event.ticket_id:04d}",
                ticket_title=ticket.title if ticket else "Ticket non disponibile",
                actor_name=actor_name,
                actor_label=actor_label,
                actor_class=event.actor_type.value,
                event_label=EVENT_TYPE_LABELS[event.event_type],
                summary=event.summary,
                detail_items=tuple(
                    AuditDetailItem(
                        DETAIL_LABELS[key],
                        _display_value(key, value, users_by_id),
                    )
                    for key, value in details.items()
                    if key in DETAIL_LABELS
                    and not (key in {"reference", "error_code"} and not value)
                ),
                created_date=event.created_at.strftime("%d/%m/%Y"),
                created_time=event.created_at.strftime("%H:%M:%S"),
            )
        )
    return views
