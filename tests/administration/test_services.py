"""Verifica il ripristino completo e controllato del dataset demo."""

import secrets
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.administration import DemoResetError, DemoResetResult, reset_demo_dataset
from app.db import (
    Attachment,
    AuditEvent,
    KnowledgeDocument,
    ProposedAction,
    Ticket,
    User,
    build_engine,
    create_database,
    seed_demo_data,
)
from app.domain.vocabulary import ActionStatus, AttachmentContextType, Priority, Role


@pytest.fixture
def reset_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'admin-reset.db'}")
    create_database(engine)
    passwords = {role: secrets.token_urlsafe(24) for role in Role}
    storage_directory = tmp_path / "knowledge"
    storage_directory.mkdir()
    attachment_storage_directory = tmp_path / "attachments"
    attachment_storage_directory.mkdir()
    with Session(engine) as session:
        seed_demo_data(session, passwords)
        session.commit()
        admin = session.scalar(select(User.id).where(User.email == "admin@servicepilot.example"))
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
        attachment_file = attachment_storage_directory / "reset-attachment.log"
        attachment_file.write_text("Log fittizio del reset.", encoding="utf-8")
        session.add(
            Attachment(
                context_type=AttachmentContextType.TICKET,
                context_id=ticket.id,
                owner_user_id=admin,
                original_filename="diagnostica.log",
                storage_filename=attachment_file.name,
                content_type="text/plain",
                size_bytes=attachment_file.stat().st_size,
                checksum_sha256="b" * 64,
            )
        )
        ticket.priority = Priority.P4
        action = session.scalar(select(ProposedAction).limit(1))
        action.status = ActionStatus.REJECTED
        session.commit()
        yield (
            session,
            passwords,
            storage_directory,
            attachment_storage_directory,
            stored_file,
            attachment_file,
        )
    engine.dispose()


def test_reset_replaces_operational_data_and_removes_stored_documents(
    reset_context,
) -> None:
    (
        session,
        passwords,
        storage_directory,
        attachment_storage_directory,
        stored_file,
        attachment_file,
    ) = reset_context

    result = reset_demo_dataset(
        session,
        passwords,
        storage_directory,
        attachment_storage_directory,
    )

    assert result == DemoResetResult(
        tickets=6,
        actions=3,
        audit_events=9,
        removed_documents=1,
        removed_files=2,
        file_cleanup_failures=0,
    )
    assert not stored_file.exists()
    assert not attachment_file.exists()
    assert session.scalar(select(func.count()).select_from(Attachment)) == 0
    assert session.scalar(select(func.count()).select_from(KnowledgeDocument)) == 0
    assert all(
        action.status is ActionStatus.PENDING_APPROVAL
        for action in session.scalars(select(ProposedAction)).all()
    )
    assert session.scalar(select(func.count()).select_from(AuditEvent)) == 9


def test_invalid_password_configuration_stops_before_reset(reset_context) -> None:
    session, _, storage_directory, _, stored_file, attachment_file = reset_context
    before_tickets = session.scalar(select(func.count()).select_from(Ticket))

    with pytest.raises(ValueError):
        reset_demo_dataset(session, {}, storage_directory)

    assert session.scalar(select(func.count()).select_from(Ticket)) == before_tickets
    assert session.scalar(select(func.count()).select_from(KnowledgeDocument)) == 1
    assert stored_file.exists()
    assert session.scalar(select(func.count()).select_from(Attachment)) == 1
    assert attachment_file.exists()


def test_reset_reports_attachment_cleanup_failure_without_claiming_success(
    reset_context, monkeypatch
) -> None:
    (
        session,
        passwords,
        storage_directory,
        attachment_storage_directory,
        stored_file,
        attachment_file,
    ) = reset_context
    original_unlink = Path.unlink

    def fail_attachment_unlink(path: Path, *args, **kwargs) -> None:
        if path == attachment_file:
            raise OSError("disco simulato non disponibile")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_attachment_unlink)

    with pytest.raises(DemoResetError, match="metadati restano disponibili"):
        reset_demo_dataset(
            session,
            passwords,
            storage_directory,
            attachment_storage_directory,
        )

    assert not stored_file.exists()
    assert attachment_file.exists()
    assert session.scalar(select(func.count()).select_from(Attachment)) == 1

    monkeypatch.undo()
    result = reset_demo_dataset(
        session,
        passwords,
        storage_directory,
        attachment_storage_directory,
    )

    assert result.removed_files == 1
    assert result.file_cleanup_failures == 0
    assert not attachment_file.exists()
    assert session.scalar(select(func.count()).select_from(Attachment)) == 0
