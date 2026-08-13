"""Operazioni distruttive riservate all'amministratore della demo."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.demo_data import seed_demo_data
from app.db.models import (
    Attachment,
    AuditEvent,
    KnowledgeDocument,
    KnowledgeSegment,
    ProposedAction,
    Ticket,
    TicketSolutionSource,
)
from app.domain.vocabulary import Role
from app.security.demo_credentials import validate_demo_passwords

DEMO_RESET_CONFIRMATION = "RIPRISTINA DEMO"


class DemoResetError(RuntimeError):
    """Il dataset non può essere ripristinato senza lasciare risultati parziali."""


@dataclass(frozen=True)
class DemoResetResult:
    """Riepilogo sicuro dell'operazione mostrabile nell'interfaccia."""

    tickets: int
    actions: int
    audit_events: int
    removed_documents: int
    removed_files: int
    file_cleanup_failures: int


def _safe_document_path(storage_directory: Path, storage_filename: str) -> Path | None:
    """Accetta soltanto nomi semplici contenuti nella cartella configurata."""

    if not storage_filename or Path(storage_filename).name != storage_filename:
        return None
    root = storage_directory.resolve()
    candidate = (root / storage_filename).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _remove_stored_files(
    storage_directory: Path,
    storage_filenames: list[str],
) -> tuple[int, int]:
    removed = 0
    failures = 0
    for storage_filename in storage_filenames:
        path = _safe_document_path(storage_directory, storage_filename)
        if path is None:
            failures += 1
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError:
            failures += 1
        else:
            removed += 1
    return removed, failures


def reset_demo_dataset(
    session: Session,
    demo_passwords: Mapping[Role, str],
    storage_directory: Path,
    attachment_storage_directory: Path | None = None,
) -> DemoResetResult:
    """Sostituisce i dati operativi con il dataset demo in una sola transazione."""

    validated_passwords = validate_demo_passwords(demo_passwords)
    storage_filenames = list(session.scalars(select(KnowledgeDocument.storage_filename)).all())
    attachment_storage_directory = (
        attachment_storage_directory or storage_directory.parent / "attachments"
    )
    attachment_filenames = list(session.scalars(select(Attachment.storage_filename)).all())
    removed_documents = len(storage_filenames)

    try:
        # L'ordine rispetta i collegamenti: prima i figli, poi ticket e documenti.
        session.execute(delete(AuditEvent))
        session.execute(delete(TicketSolutionSource))
        session.execute(delete(ProposedAction))
        session.execute(delete(Attachment))
        session.execute(delete(KnowledgeSegment))
        session.execute(delete(KnowledgeDocument))
        session.execute(delete(Ticket))
        # Le chiavi SQLite possono essere riutilizzate: scartiamo le vecchie istanze
        # dalla memoria della sessione prima di creare i nuovi record demo.
        session.expunge_all()
        seed_demo_data(session, validated_passwords)
        session.commit()
    except Exception as error:
        session.rollback()
        raise DemoResetError(
            "Il ripristino è stato annullato: i dati precedenti non sono stati modificati."
        ) from error

    removed_files, cleanup_failures = _remove_stored_files(
        storage_directory,
        storage_filenames,
    )
    removed_attachment_files, attachment_cleanup_failures = _remove_stored_files(
        attachment_storage_directory,
        attachment_filenames,
    )
    return DemoResetResult(
        tickets=session.scalar(select(func.count()).select_from(Ticket)) or 0,
        actions=session.scalar(select(func.count()).select_from(ProposedAction)) or 0,
        audit_events=session.scalar(select(func.count()).select_from(AuditEvent)) or 0,
        removed_documents=removed_documents,
        removed_files=removed_files + removed_attachment_files,
        file_cleanup_failures=cleanup_failures + attachment_cleanup_failures,
    )
