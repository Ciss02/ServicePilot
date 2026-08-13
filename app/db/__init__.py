"""Accesso pubblico alla persistenza di ServicePilot."""

from app.db.base import Base
from app.db.demo_data import SeedSummary, load_demo_data, seed_demo_data
from app.db.models import (
    Attachment,
    AuditEvent,
    AuthSession,
    KnowledgeDocument,
    KnowledgeSegment,
    ProposedAction,
    Site,
    Ticket,
    TicketSolutionSource,
    User,
)
from app.db.session import SessionLocal, build_engine, create_database, engine, get_session

__all__ = [
    "Base",
    "AuthSession",
    "Attachment",
    "AuditEvent",
    "KnowledgeDocument",
    "KnowledgeSegment",
    "ProposedAction",
    "SessionLocal",
    "SeedSummary",
    "Site",
    "Ticket",
    "TicketSolutionSource",
    "User",
    "build_engine",
    "create_database",
    "engine",
    "get_session",
    "load_demo_data",
    "seed_demo_data",
]
