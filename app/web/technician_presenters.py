"""Prepara dati e filtri della coda tecnica per le pagine web."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Site, Ticket, User
from app.domain.vocabulary import Impact, Priority, Role, TicketCategory, TicketStatus, Urgency
from app.web.ticket_presenters import CATEGORY_LABELS, PRIORITY_LABELS, STATUS_LABELS


TechnicianStatusFilter = Literal[
    "open", "waiting", "completed", "new", "in_progress",
    "waiting_for_requester", "waiting_for_vendor", "resolved", "closed",
]
TechnicianAssignmentFilter = Literal["all", "mine", "unassigned"]
TechnicianPriorityFilter = Literal["all", "p1", "p2", "p3", "p4", "pending"]
TechnicianSort = Literal["priority", "newest", "oldest", "updated"]

IMPACT_LABELS = {Impact.LOW: "Basso", Impact.MEDIUM: "Medio", Impact.HIGH: "Alto"}
URGENCY_LABELS = {Urgency.LOW: "Bassa", Urgency.MEDIUM: "Media", Urgency.HIGH: "Alta"}


@dataclass(frozen=True)
class TechnicianTicketView:
    """Ticket completo con testi pronti per coda e dettaglio tecnico."""

    id: int
    code: str
    title: str
    description: str
    requester_name: str
    requester_email: str
    site_name: str
    service: str
    affected_users_label: str
    category_code: str
    category_label: str
    subcategory: str
    impact_code: str
    impact_label: str
    urgency_code: str
    urgency_label: str
    priority_code: str
    priority_label: str
    assigned_group: str
    classification_review_status: str
    assigned_technician_id: int | None
    technician_name: str
    status_code: str
    status_label: str
    technician_note: str
    resolution: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TechnicianQueueSummary:
    """Numeri utili per capire subito il carico della coda."""

    open: int
    unassigned: int
    waiting: int
    completed: int


def _format_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y · %H:%M")


def present_technician_tickets(
    session: Session,
    tickets: list[Ticket],
) -> list[TechnicianTicketView]:
    """Carica insieme i riferimenti e converte i codici in testi italiani."""

    site_ids = {ticket.site_id for ticket in tickets}
    user_ids = {ticket.requester_id for ticket in tickets}
    user_ids.update(
        ticket.assigned_technician_id
        for ticket in tickets
        if ticket.assigned_technician_id is not None
    )
    sites = (
        list(session.scalars(select(Site).where(Site.id.in_(site_ids))).all())
        if site_ids
        else []
    )
    users = (
        list(session.scalars(select(User).where(User.id.in_(user_ids))).all())
        if user_ids
        else []
    )
    sites_by_id = {site.id: site.name for site in sites}
    users_by_id = {user.id: user for user in users}

    views: list[TechnicianTicketView] = []
    for ticket in tickets:
        requester = users_by_id.get(ticket.requester_id)
        technician = users_by_id.get(ticket.assigned_technician_id)
        views.append(
            TechnicianTicketView(
                id=ticket.id,
                code=f"SP-{ticket.id:04d}",
                title=ticket.title,
                description=ticket.description,
                requester_name=(
                    requester.display_name
                    if requester
                    else "Richiedente non disponibile"
                ),
                requester_email=requester.email if requester else "—",
                site_name=sites_by_id.get(ticket.site_id, "Sede non disponibile"),
                service=ticket.service,
                affected_users_label=(
                    "1 persona"
                    if ticket.affected_users == 1
                    else f"{ticket.affected_users} persone"
                ),
                category_code=ticket.category.value if ticket.category else "",
                category_label=(
                    CATEGORY_LABELS[ticket.category]
                    if ticket.category
                    else "Da classificare"
                ),
                subcategory=ticket.subcategory or "",
                impact_code=ticket.impact.value if ticket.impact else "",
                impact_label=(
                    IMPACT_LABELS[ticket.impact] if ticket.impact else "Da definire"
                ),
                urgency_code=ticket.urgency.value if ticket.urgency else "",
                urgency_label=(
                    URGENCY_LABELS[ticket.urgency] if ticket.urgency else "Da definire"
                ),
                priority_code=ticket.priority.value if ticket.priority else "pending",
                priority_label=(
                    PRIORITY_LABELS[ticket.priority]
                    if ticket.priority
                    else "Priorità da calcolare"
                ),
                assigned_group=ticket.assigned_group or "",
                classification_review_status=ticket.classification_review_status.value,
                assigned_technician_id=ticket.assigned_technician_id,
                technician_name=(
                    technician.display_name if technician else "Non assegnato"
                ),
                status_code=ticket.status.value,
                status_label=STATUS_LABELS[ticket.status],
                technician_note=ticket.technician_note or "",
                resolution=ticket.resolution or "",
                created_at=_format_datetime(ticket.created_at),
                updated_at=_format_datetime(ticket.updated_at),
            )
        )
    return views


def filter_and_sort_technician_tickets(
    tickets: list[Ticket],
    *,
    current_user_id: int,
    status_filter: TechnicianStatusFilter,
    assignment_filter: TechnicianAssignmentFilter,
    priority_filter: TechnicianPriorityFilter,
    sort_by: TechnicianSort,
) -> list[Ticket]:
    """Applica i filtri scelti senza modificare i record salvati."""

    filtered = list(tickets)
    if status_filter == "open":
        filtered = [
            ticket
            for ticket in filtered
            if ticket.status not in {TicketStatus.RESOLVED, TicketStatus.CLOSED}
        ]
    elif status_filter == "waiting":
        filtered = [
            ticket
            for ticket in filtered
            if ticket.status
            in {TicketStatus.WAITING_FOR_REQUESTER, TicketStatus.WAITING_FOR_VENDOR}
        ]
    elif status_filter == "completed":
        filtered = [
            ticket
            for ticket in filtered
            if ticket.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}
        ]
    else:
        filtered = [ticket for ticket in filtered if ticket.status.value == status_filter]
    if assignment_filter == "mine":
        filtered = [
            ticket
            for ticket in filtered
            if ticket.assigned_technician_id == current_user_id
        ]
    elif assignment_filter == "unassigned":
        filtered = [ticket for ticket in filtered if ticket.assigned_technician_id is None]
    if priority_filter == "pending":
        filtered = [ticket for ticket in filtered if ticket.priority is None]
    elif priority_filter != "all":
        filtered = [
            ticket
            for ticket in filtered
            if ticket.priority and ticket.priority.value == priority_filter
        ]

    if sort_by == "oldest":
        return sorted(filtered, key=lambda ticket: (ticket.created_at, ticket.id))
    if sort_by == "updated":
        return sorted(
            filtered,
            key=lambda ticket: (ticket.updated_at, ticket.id),
            reverse=True,
        )
    if sort_by == "priority":
        order = {
            Priority.P1: 0,
            Priority.P2: 1,
            Priority.P3: 2,
            Priority.P4: 3,
            None: 4,
        }
        return sorted(
            filtered,
            key=lambda ticket: (
                order[ticket.priority],
                -ticket.created_at.timestamp(),
                -ticket.id,
            ),
        )
    return sorted(filtered, key=lambda ticket: (ticket.created_at, ticket.id), reverse=True)


def summarize_technician_queue(tickets: list[Ticket]) -> TechnicianQueueSummary:
    """Conta ticket aperti, non assegnati, in attesa e completati."""

    completed = {TicketStatus.RESOLVED, TicketStatus.CLOSED}
    waiting = {TicketStatus.WAITING_FOR_REQUESTER, TicketStatus.WAITING_FOR_VENDOR}
    return TechnicianQueueSummary(
        open=sum(ticket.status not in completed for ticket in tickets),
        unassigned=sum(ticket.assigned_technician_id is None for ticket in tickets),
        waiting=sum(ticket.status in waiting for ticket in tickets),
        completed=sum(ticket.status in completed for ticket in tickets),
    )


def list_active_technical_users(session: Session) -> list[User]:
    """Restituisce tecnici e amministratori attivi in ordine alfabetico."""

    return list(
        session.scalars(
            select(User)
            .where(User.role.in_({Role.TECHNICIAN, Role.ADMIN}), User.is_active.is_(True))
            .order_by(User.display_name)
        ).all()
    )


CATEGORY_OPTIONS = tuple((item.value, CATEGORY_LABELS[item]) for item in TicketCategory)
IMPACT_OPTIONS = tuple((item.value, IMPACT_LABELS[item]) for item in Impact)
URGENCY_OPTIONS = tuple((item.value, URGENCY_LABELS[item]) for item in Urgency)
STATUS_OPTIONS = tuple((item.value, STATUS_LABELS[item]) for item in TicketStatus)
