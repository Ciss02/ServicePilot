"""Gestione amministrativa dei documenti già conservati."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import KnowledgeDocument
from app.knowledge.extraction import invalidate_solutions_for_document


class KnowledgeDocumentNotFoundError(LookupError):
    """Il documento richiesto non esiste più."""


class KnowledgeDocumentDeletionError(RuntimeError):
    """Il documento non è stato eliminato in modo completo dal database."""


@dataclass(frozen=True)
class DocumentDeletionResult:
    """Esito dell'eliminazione senza esporre il nome interno del file."""

    filename: str
    stored_file_removed: bool


def _safe_stored_path(document: KnowledgeDocument, storage_directory: Path) -> Path:
    if Path(document.storage_filename).name != document.storage_filename:
        raise KnowledgeDocumentDeletionError("Il percorso interno del documento non è valido.")
    root = storage_directory.resolve()
    path = (root / document.storage_filename).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise KnowledgeDocumentDeletionError(
            "Il percorso interno del documento non è valido."
        ) from error
    return path


def delete_knowledge_document(
    session: Session,
    document_id: int,
    storage_directory: Path,
) -> DocumentDeletionResult:
    """Elimina metadati e segmenti prima di rimuovere il file locale."""

    document = session.get(KnowledgeDocument, document_id)
    if document is None:
        raise KnowledgeDocumentNotFoundError
    stored_path = _safe_stored_path(document, storage_directory)
    original_filename = document.original_filename

    try:
        invalidate_solutions_for_document(session, document.id)
        session.delete(document)
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise KnowledgeDocumentDeletionError(
            "Il documento non è stato eliminato: nessun dato è stato modificato."
        ) from error

    try:
        stored_path.unlink(missing_ok=True)
    except OSError:
        file_removed = False
    else:
        file_removed = True
    return DocumentDeletionResult(
        filename=original_filename,
        stored_file_removed=file_removed,
    )
