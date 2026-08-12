"""Validazione e salvataggio sicuro dei documenti della knowledge base."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import KnowledgeDocument, User


MAX_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_DOCUMENT_EXTENSIONS = frozenset({".pdf", ".md", ".markdown"})
PDF_CONTENT_TYPES = frozenset({"application/pdf", "application/octet-stream"})
MARKDOWN_CONTENT_TYPES = frozenset(
    {"text/markdown", "text/plain", "application/octet-stream"}
)
READ_CHUNK_SIZE = 64 * 1024


class KnowledgeDocumentValidationError(ValueError):
    """Il file non rispetta le regole di sicurezza dell'upload."""


class KnowledgeDocumentPersistenceError(RuntimeError):
    """Il documento valido non ha potuto essere conservato per intero."""


def _safe_original_filename(raw_filename: str | None) -> tuple[str, str]:
    """Riduce il nome al solo file e controlla l'estensione ammessa."""

    if not raw_filename:
        raise KnowledgeDocumentValidationError("Seleziona un documento da caricare.")

    filename = Path(raw_filename.replace("\\", "/")).name.strip()
    if not filename or filename in {".", ".."}:
        raise KnowledgeDocumentValidationError("Il nome del documento non è valido.")
    if len(filename) > 255 or any(ord(character) < 32 for character in filename):
        raise KnowledgeDocumentValidationError(
            "Il nome del documento è troppo lungo o contiene caratteri non validi."
        )

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise KnowledgeDocumentValidationError(
            "Formato non ammesso. Carica un file PDF oppure Markdown (.md)."
        )
    return filename, extension


def _normalized_content_type(content_type: str | None) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def _read_limited(upload: UploadFile) -> bytes:
    """Legge al massimo il limite più un byte, così i file enormi non entrano in memoria."""

    parts: list[bytes] = []
    total_size = 0
    upload.file.seek(0)
    while total_size <= MAX_DOCUMENT_SIZE_BYTES:
        chunk = upload.file.read(
            min(READ_CHUNK_SIZE, MAX_DOCUMENT_SIZE_BYTES + 1 - total_size)
        )
        if not chunk:
            break
        parts.append(chunk)
        total_size += len(chunk)

    if total_size > MAX_DOCUMENT_SIZE_BYTES:
        raise KnowledgeDocumentValidationError(
            "Il documento supera il limite massimo di 5 MB."
        )
    if total_size == 0:
        raise KnowledgeDocumentValidationError("Il documento è vuoto.")
    return b"".join(parts)


def _validate_content(extension: str, content_type: str, content: bytes) -> str:
    """Confronta estensione, tipo dichiarato e contenuto reale."""

    if extension == ".pdf":
        if content_type not in PDF_CONTENT_TYPES:
            raise KnowledgeDocumentValidationError(
                "Il tipo dichiarato non corrisponde a un documento PDF."
            )
        if not content.startswith(b"%PDF-"):
            raise KnowledgeDocumentValidationError(
                "Il file non contiene un documento PDF riconoscibile."
            )
        return "application/pdf"

    if content_type not in MARKDOWN_CONTENT_TYPES:
        raise KnowledgeDocumentValidationError(
            "Il tipo dichiarato non corrisponde a un documento Markdown."
        )
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise KnowledgeDocumentValidationError(
            "Il file Markdown deve contenere testo UTF-8 valido."
        ) from error
    if "\x00" in text:
        raise KnowledgeDocumentValidationError(
            "Il file Markdown contiene dati binari non ammessi."
        )
    return "text/markdown"


def store_knowledge_document(
    session: Session,
    upload: UploadFile,
    uploaded_by: User,
    storage_directory: Path,
) -> KnowledgeDocument:
    """Valida e conserva file e metadati, ripulendo gli eventuali salvataggi parziali."""

    try:
        original_filename, extension = _safe_original_filename(upload.filename)
        content = _read_limited(upload)
        content_type = _validate_content(
            extension,
            _normalized_content_type(upload.content_type),
            content,
        )
    except Exception:
        upload.file.close()
        raise

    stored_extension = ".pdf" if extension == ".pdf" else ".md"
    storage_filename = f"{uuid4().hex}{stored_extension}"
    final_path = storage_directory / storage_filename
    temporary_path: Path | None = None

    try:
        storage_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=storage_directory,
            prefix=".upload-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, final_path)
        temporary_path = None

        document = KnowledgeDocument(
            original_filename=original_filename,
            storage_filename=storage_filename,
            content_type=content_type,
            size_bytes=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            uploaded_by_user_id=uploaded_by.id,
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        return document
    except (OSError, SQLAlchemyError) as error:
        session.rollback()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise KnowledgeDocumentPersistenceError(
            "Non siamo riusciti a conservare il documento. Riprova tra poco."
        ) from error
    finally:
        upload.file.close()
