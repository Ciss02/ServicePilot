"""Trasforma i ticket nei testi chiari mostrati dall'interfaccia web."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.db.models import Ticket
from app.domain.vocabulary import Priority, TicketCategory, TicketStatus

EmployeeTicketFilter = Literal["all", "active", "waiting", "completed"]


STATUS_LABELS = {
    TicketStatus.NEW: "Aperto",
    TicketStatus.IN_PROGRESS: "In lavorazione",
    TicketStatus.WAITING_FOR_REQUESTER: "In attesa di te",
    TicketStatus.WAITING_FOR_VENDOR: "In attesa del fornitore",
    TicketStatus.RESOLVED: "Risolto",
    TicketStatus.CLOSED: "Chiuso",
}

CATEGORY_LABELS = {
    TicketCategory.ACCOUNT_AND_ACCESS: "Account e accessi",
    TicketCategory.DEVICES_AND_HARDWARE: "Dispositivi e hardware",
    TicketCategory.SOFTWARE_AND_APPLICATIONS: "Software e applicazioni",
    TicketCategory.NETWORK_AND_CONNECTIVITY: "Rete e connettività",
    TicketCategory.PRINTERS_AND_LABELING: "Stampanti ed etichettatura",
    TicketCategory.TELEPHONY: "Telefonia",
    TicketCategory.RETAIL_SYSTEMS: "Sistemi di negozio",
    TicketCategory.PRODUCTION_SYSTEMS: "Sistemi produttivi",
    TicketCategory.INFORMATION_SECURITY: "Sicurezza informatica",
    TicketCategory.OTHER_REQUESTS: "Altre richieste",
}

PRIORITY_LABELS = {
    Priority.P1: "P1 · Critica",
    Priority.P2: "P2 · Alta",
    Priority.P3: "P3 · Media",
    Priority.P4: "P4 · Bassa",
}


@dataclass(frozen=True)
class EmployeeTicketView:
    """Dati già pronti per elenco e dettaglio del dipendente."""

    id: int
    code: str
    title: str
    description: str
    status_code: str
    status_label: str
    priority_code: str
    priority_label: str
    category_label: str
    site_name: str
    service: str
    affected_users_label: str
    assigned_group: str
    technician_name: str
    technician_note: str | None
    resolution: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EmployeeTicketSummary:
    """Conteggi sintetici dell'area personale."""

    active: int
    waiting_for_requester: int
    completed: int


def _format_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y · %H:%M")


def present_employee_ticket(
    ticket: Ticket,
    *,
    site_name: str,
    technician_name: str,
) -> EmployeeTicketView:
    """Converte codici tecnici e valori mancanti in testi comprensibili."""

    priority_code = ticket.priority.value if ticket.priority else "pending"
    return EmployeeTicketView(
        id=ticket.id,
        code=f"SP-{ticket.id:04d}",
        title=ticket.title,
        description=ticket.description,
        status_code=ticket.status.value,
        status_label=STATUS_LABELS[ticket.status],
        priority_code=priority_code,
        priority_label=(
            PRIORITY_LABELS[ticket.priority] if ticket.priority else "Priorità da calcolare"
        ),
        category_label=(CATEGORY_LABELS[ticket.category] if ticket.category else "Da classificare"),
        site_name=site_name,
        service=ticket.service,
        affected_users_label=(
            "1 persona" if ticket.affected_users == 1 else f"{ticket.affected_users} persone"
        ),
        assigned_group=ticket.assigned_group or "Non ancora assegnato",
        technician_name=technician_name,
        technician_note=ticket.technician_note,
        resolution=ticket.resolution,
        created_at=_format_datetime(ticket.created_at),
        updated_at=_format_datetime(ticket.updated_at),
    )


def summarize_employee_tickets(tickets: list[Ticket]) -> EmployeeTicketSummary:
    """Conta richieste attive, in attesa del dipendente e completate."""

    completed_statuses = {TicketStatus.RESOLVED, TicketStatus.CLOSED}
    return EmployeeTicketSummary(
        active=sum(ticket.status not in completed_statuses for ticket in tickets),
        waiting_for_requester=sum(
            ticket.status is TicketStatus.WAITING_FOR_REQUESTER for ticket in tickets
        ),
        completed=sum(ticket.status in completed_statuses for ticket in tickets),
    )


def filter_employee_tickets(
    tickets: list[Ticket],
    selected_filter: EmployeeTicketFilter,
) -> list[Ticket]:
    """Filtra la vista senza modificare i ticket o i conteggi complessivi."""

    completed_statuses = {TicketStatus.RESOLVED, TicketStatus.CLOSED}
    if selected_filter == "active":
        return [ticket for ticket in tickets if ticket.status not in completed_statuses]
    if selected_filter == "waiting":
        return [ticket for ticket in tickets if ticket.status is TicketStatus.WAITING_FOR_REQUESTER]
    if selected_filter == "completed":
        return [ticket for ticket in tickets if ticket.status in completed_statuses]
    return tickets
