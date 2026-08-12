"""Verifica persistenza atomica, dettagli controllati e immutabilità."""

import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import list_ticket_audit_events
from app.db import AuditEvent, Site, User, build_engine, create_database
from app.domain.ticket_contracts import TicketCreate, TicketUpdate
from app.domain.vocabulary import AuditEventType, Role, TicketStatus
from app.tickets.creation import create_confirmed_ticket
from app.tickets.management import (
    ManagedTechnicianNotFoundError,
    update_managed_ticket,
)


@pytest.fixture
def audit_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'audit-events.db'}")
    create_database(engine)
    with Session(engine) as session:
        requester = User(
            email="richiedente.audit@example.test",
            display_name="Richiedente Audit Demo",
            role=Role.EMPLOYEE,
        )
        technician = User(
            email="tecnico.audit@example.test",
            display_name="Tecnico Audit Demo",
            role=Role.TECHNICIAN,
        )
        site = Site(code="AUDIT-DEMO", name="Sede Audit Demo")
        session.add_all([requester, technician, site])
        session.commit()
        context = {
            "requester_id": requester.id,
            "technician_id": technician.id,
            "site_id": site.id,
        }
    yield engine, context
    engine.dispose()


def _create_ticket(session: Session, context: dict):
    return create_confirmed_ticket(
        session,
        TicketCreate(
            title="Ticket demo con audit",
            description="Richiesta completamente fittizia per verificare la cronologia.",
            site_id=context["site_id"],
            service="Servizio audit demo",
            affected_users=2,
            confirmed=True,
        ),
        session.get(User, context["requester_id"]),
    )


def test_creation_and_update_build_a_readable_ticket_path(audit_context) -> None:
    engine, context = audit_context
    with Session(engine) as session:
        ticket = _create_ticket(session, context)
        update_managed_ticket(
            session,
            ticket.id,
            TicketUpdate(
                status=TicketStatus.IN_PROGRESS,
                assigned_group="Supporto audit demo",
                assigned_technician_id=context["technician_id"],
                technician_note="Dettaglio operativo che non va copiato nell'audit.",
            ),
            updated_by=session.get(User, context["technician_id"]),
        )

        events = list_ticket_audit_events(session, ticket.id)
        assert [event.event_type for event in events] == [
            AuditEventType.TICKET_CREATED,
            AuditEventType.TICKET_STATUS_CHANGED,
            AuditEventType.TICKET_ASSIGNMENT_CHANGED,
            AuditEventType.TICKET_UPDATED,
        ]
        assert events[0].actor_user_id == context["requester_id"]
        assert all(event.ticket_id == ticket.id for event in events)
        details = json.loads(events[-1].details_json)
        assert details == {"changed_fields": ["technician_note"]}
        assert "Dettaglio operativo" not in events[-1].details_json


def test_audit_events_cannot_be_updated_or_deleted(audit_context) -> None:
    engine, context = audit_context
    with Session(engine) as session:
        ticket = _create_ticket(session, context)
        event = session.scalar(
            select(AuditEvent).where(AuditEvent.ticket_id == ticket.id)
        )
        original_summary = event.summary
        event.summary = "Tentativo di riscrittura"
        with pytest.raises(ValueError, match="append-only"):
            session.commit()
        session.rollback()

        event = session.get(AuditEvent, event.id)
        assert event.summary == original_summary
        session.delete(event)
        with pytest.raises(ValueError, match="append-only"):
            session.commit()
        session.rollback()
        assert session.get(AuditEvent, event.id) is not None


def test_rejected_ticket_update_does_not_create_an_audit_event(audit_context) -> None:
    engine, context = audit_context
    with Session(engine) as session:
        ticket = _create_ticket(session, context)
        with pytest.raises(ManagedTechnicianNotFoundError):
            update_managed_ticket(
                session,
                ticket.id,
                TicketUpdate(assigned_technician_id=999_999),
                updated_by=session.get(User, context["technician_id"]),
            )

        events = list_ticket_audit_events(session, ticket.id)
        assert [event.event_type for event in events] == [
            AuditEventType.TICKET_CREATED
        ]
