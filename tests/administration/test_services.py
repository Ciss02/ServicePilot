"""Verifica il ripristino completo e controllato del dataset demo."""

import secrets

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.administration import DemoResetResult, reset_demo_dataset
from app.db import (
    AuditEvent,
    KnowledgeDocument,
    ProposedAction,
    Ticket,
    User,
    build_engine,
    create_database,
    seed_demo_data,
)
from app.domain.vocabulary import ActionStatus, Priority, Role


@pytest.fixture
def reset_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'admin-reset.db'}")
    create_database(engine)
    passwords = {role: secrets.token_urlsafe(24) for role in Role}
    storage_directory = tmp_path / "knowledge"
    storage_directory.mkdir()
    with Session(engine) as session:
        seed_demo_data(session, passwords)
        session.commit()
        admin = session.scalar(
            select(User.id).where(User.email == "admin@servicepilot.example")
        )
        stored_file = storage_directory / "reset-demo.md"
        stored_file.write_text("# Demo\n\nContenuto fittizio.", encoding="utf-8")
        session.add(
            KnowledgeDocument(
                original_filename="reset-demo.md",
                storage_filename=stored_file.name,
                content_type="text/markdown",
                size_bytes=stored_file.stat().st_size,
                checksum_sha256="a" * 64,
                uploaded_by_user_id=admin,
            )
        )
        ticket = session.scalar(select(Ticket).limit(1))
        ticket.priority = Priority.P4
        action = session.scalar(select(ProposedAction).limit(1))
        action.status = ActionStatus.REJECTED
        session.commit()
        yield session, passwords, storage_directory, stored_file
    engine.dispose()


def test_reset_replaces_operational_data_and_removes_stored_documents(
    reset_context,
) -> None:
    session, passwords, storage_directory, stored_file = reset_context

    result = reset_demo_dataset(session, passwords, storage_directory)

    assert result == DemoResetResult(
        tickets=6,
        actions=3,
        audit_events=9,
        removed_documents=1,
        removed_files=1,
        file_cleanup_failures=0,
    )
    assert not stored_file.exists()
    assert session.scalar(select(func.count()).select_from(KnowledgeDocument)) == 0
    assert all(
        action.status is ActionStatus.PENDING_APPROVAL
        for action in session.scalars(select(ProposedAction)).all()
    )
    assert session.scalar(select(func.count()).select_from(AuditEvent)) == 9


def test_invalid_password_configuration_stops_before_reset(reset_context) -> None:
    session, _, storage_directory, stored_file = reset_context
    before_tickets = session.scalar(select(func.count()).select_from(Ticket))

    with pytest.raises(ValueError):
        reset_demo_dataset(session, {}, storage_directory)

    assert session.scalar(select(func.count()).select_from(Ticket)) == before_tickets
    assert session.scalar(select(func.count()).select_from(KnowledgeDocument)) == 1
    assert stored_file.exists()
