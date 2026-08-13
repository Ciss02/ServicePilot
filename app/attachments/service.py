"""Validazione, conservazione e accesso autorizzato agli allegati privati."""

from __future__ import annotations

import hashlib
import logging
import os
import re
import tempfile
import unicodedata
import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Attachment, Ticket, User
from app.domain.vocabulary import AttachmentContextType
from app.tickets.queries import get_visible_ticket

MAX_ATTACHMENTS_PER_REQUEST = 5
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024
MAX_CONTEXT_SIZE_BYTES = 100 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
READ_CHUNK_SIZE = 64 * 1024
_TEXT_EXTENSIONS = frozenset({".txt", ".log"})
_TEXT_CONTENT_TYPES = frozenset({"text/plain", "application/octet-stream"})
_IMAGE_FORMATS = {
    ".png": ("image/png", "PNG"),
    ".jpg": ("image/jpeg", "JPEG"),
    ".jpeg": ("image/jpeg", "JPEG"),
}
_DANGEROUS_TEXT_MARKUP = re.compile(
    r"<\s*(?:!|\?|/?[a-z][a-z0-9:-]*(?:\s|/?>))",
    re.IGNORECASE,
)
LOGGER = logging.getLogger(__name__)


class AttachmentValidationError(ValueError):
    """Il file non soddisfa le regole di sicurezza dell'archivio."""


class AttachmentPersistenceError(RuntimeError):
    """Un allegato valido non ha potuto essere conservato completamente."""


class AttachmentNotFoundError(LookupError):
    """L'allegato non esiste o non è visibile all'utente corrente."""


class AttachmentStorageError(RuntimeError):
    """Il metadato esiste ma il file privato non è più disponibile."""


@dataclass(frozen=True)
class AttachmentContext:
    """Contesto creato dal backend, mai da campi liberi inviati dal browser."""

    type: AttachmentContextType
    id: int

    def __post_init__(self) -> None:
        if self.id < 1:
            raise ValueError("L'identificativo del contesto deve essere positivo.")


@dataclass(frozen=True)
class _ValidatedAttachment:
    original_filename: str
    content_type: str
    content: bytes


def _safe_original_filename(raw_filename: str | None) -> tuple[str, str]:
    if not raw_filename:
        raise AttachmentValidationError("Seleziona almeno un allegato.")
    filename = Path(raw_filename.replace("\\", "/")).name.strip()
    if not filename or filename in {".", ".."}:
        raise AttachmentValidationError("Il nome dell'allegato non è valido.")
    if len(filename) > 255 or any(
        unicodedata.category(character) in {"Cc", "Cf"} for character in filename
    ):
        raise AttachmentValidationError("Il nome dell'allegato non è valido.")
    extension = Path(filename).suffix.lower()
    if extension not in {*_TEXT_EXTENSIONS, *_IMAGE_FORMATS, ".pdf"}:
        raise AttachmentValidationError("Formato non ammesso. Usa PNG, JPEG, PDF, TXT o LOG.")
    return filename, extension


def _normalized_content_type(value: str | None) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


def _read_limited(upload: UploadFile) -> bytes:
    parts: list[bytes] = []
    size = 0
    upload.file.seek(0)
    while size <= MAX_ATTACHMENT_SIZE_BYTES:
        chunk = upload.file.read(min(READ_CHUNK_SIZE, MAX_ATTACHMENT_SIZE_BYTES + 1 - size))
        if not chunk:
            break
        parts.append(chunk)
        size += len(chunk)
    if not size:
        raise AttachmentValidationError("L'allegato è vuoto.")
    if size > MAX_ATTACHMENT_SIZE_BYTES:
        raise AttachmentValidationError("Ogni allegato può occupare al massimo 10 MB.")
    return b"".join(parts)


def _normalize_image(content: bytes, expected_format: str) -> bytes:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format != expected_format or getattr(source, "is_animated", False):
                    raise AttachmentValidationError(
                        "L'immagine non corrisponde al formato dichiarato."
                    )
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise AttachmentValidationError("L'immagine supera il limite di sicurezza.")
                source.load()
                normalized = ImageOps.exif_transpose(source)
                if expected_format == "JPEG" and normalized.mode not in {"RGB", "L"}:
                    normalized = normalized.convert("RGB")
                output = BytesIO()
                normalized.save(output, format=expected_format)
                return output.getvalue()
    except (DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise AttachmentValidationError("L'immagine supera il limite di sicurezza.") from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise AttachmentValidationError("Il file non contiene un'immagine valida.") from error


def _validate_pdf(content: bytes) -> None:
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        if reader.is_encrypted or len(reader.pages) < 1:
            raise AttachmentValidationError("Il PDF deve essere leggibile e non protetto.")
    except AttachmentValidationError:
        raise
    except (PdfReadError, EOFError, OSError, TypeError, ValueError) as error:
        raise AttachmentValidationError("Il file non contiene un PDF valido.") from error


def _validate_text(content: bytes) -> None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AttachmentValidationError("TXT e LOG devono contenere testo UTF-8 valido.") from error
    if "\x00" in text or any(ord(char) < 32 and char not in "\n\r\t" for char in text):
        raise AttachmentValidationError("TXT e LOG non possono contenere dati binari.")
    if _DANGEROUS_TEXT_MARKUP.search(text):
        raise AttachmentValidationError("Contenuti HTML o SVG non sono ammessi come allegati.")


def _remove_paths(paths: list[Path]) -> int:
    """Tenta tutta la compensazione e registra senza mascherare l'errore iniziale."""

    failures = 0
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            failures += 1
    if failures:
        LOGGER.error(
            "Pulizia incompleta dello storage allegati: %s file non rimossi.",
            failures,
        )
    return failures


def _validate_upload(upload: UploadFile) -> _ValidatedAttachment:
    filename, extension = _safe_original_filename(upload.filename)
    content = _read_limited(upload)
    declared_type = _normalized_content_type(upload.content_type)
    if extension in _IMAGE_FORMATS:
        content_type, image_format = _IMAGE_FORMATS[extension]
        if declared_type != content_type:
            raise AttachmentValidationError("Il tipo dichiarato non corrisponde all'immagine.")
        content = _normalize_image(content, image_format)
    elif extension == ".pdf":
        if declared_type != "application/pdf":
            raise AttachmentValidationError("Il tipo dichiarato non corrisponde al PDF.")
        _validate_pdf(content)
        content_type = "application/pdf"
    else:
        if declared_type not in _TEXT_CONTENT_TYPES:
            raise AttachmentValidationError("Il tipo dichiarato non corrisponde a TXT o LOG.")
        _validate_text(content)
        content_type = "text/plain"
    if len(content) > MAX_ATTACHMENT_SIZE_BYTES:
        raise AttachmentValidationError("L'allegato normalizzato supera il limite di 10 MB.")
    return _ValidatedAttachment(filename, content_type, content)


def _safe_stored_path(storage_directory: Path, storage_filename: str) -> Path:
    if not storage_filename or Path(storage_filename).name != storage_filename:
        raise AttachmentStorageError("Il riferimento interno dell'allegato non è valido.")
    root = storage_directory.resolve()
    path = (root / storage_filename).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise AttachmentStorageError(
            "Il riferimento interno dell'allegato non è valido."
        ) from error
    return path


def _context_size(session: Session, context: AttachmentContext) -> int:
    return int(
        session.scalar(
            select(func.coalesce(func.sum(Attachment.size_bytes), 0)).where(
                Attachment.context_type == context.type,
                Attachment.context_id == context.id,
            )
        )
        or 0
    )


def store_ticket_attachments(
    session: Session,
    uploads: list[UploadFile],
    ticket: Ticket,
    uploaded_by: User,
    storage_directory: Path,
) -> list[Attachment]:
    """Conserva allegati del ticket con scrittura temporanea e compensazione completa."""

    if not uploads or len(uploads) > MAX_ATTACHMENTS_PER_REQUEST:
        raise AttachmentValidationError("Puoi inviare da 1 a 5 allegati alla volta.")
    context = AttachmentContext(AttachmentContextType.TICKET, ticket.id)
    temporary_paths: list[Path] = []
    final_paths: list[Path] = []
    try:
        validated = [_validate_upload(upload) for upload in uploads]
        new_size = sum(len(item.content) for item in validated)
        if _context_size(session, context) + new_size > MAX_CONTEXT_SIZE_BYTES:
            raise AttachmentValidationError(
                "Il ticket può contenere al massimo 100 MB di allegati."
            )
        storage_directory.mkdir(parents=True, exist_ok=True)
        attachments: list[Attachment] = []
        for item in validated:
            extension = Path(item.original_filename).suffix.lower()
            stored_extension = ".jpg" if extension == ".jpeg" else extension
            storage_filename = f"{uuid4().hex}{stored_extension}"
            final_path = _safe_stored_path(storage_directory, storage_filename)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=storage_directory, prefix=".upload-", suffix=".tmp", delete=False
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_paths.append(temporary_path)
                temporary_file.write(item.content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, final_path)
            temporary_paths.remove(temporary_path)
            final_paths.append(final_path)
            attachments.append(
                Attachment(
                    context_type=context.type,
                    context_id=context.id,
                    owner_user_id=uploaded_by.id,
                    original_filename=item.original_filename,
                    storage_filename=storage_filename,
                    content_type=item.content_type,
                    size_bytes=len(item.content),
                    checksum_sha256=hashlib.sha256(item.content).hexdigest(),
                )
            )
        session.add_all(attachments)
        session.flush()
        session.commit()
        return attachments
    except AttachmentValidationError:
        session.rollback()
        _remove_paths([*temporary_paths, *final_paths])
        raise
    except Exception as error:
        session.rollback()
        cleanup_failures = _remove_paths([*temporary_paths, *final_paths])
        cleanup_note = (
            " La pulizia dello storage non è riuscita completamente." if cleanup_failures else ""
        )
        raise AttachmentPersistenceError(
            "Non siamo riusciti a conservare gli allegati. Riprova tra poco." + cleanup_note
        ) from error
    finally:
        for upload in uploads:
            try:
                upload.file.close()
            except Exception:
                LOGGER.warning("Chiusura incompleta di un file ricevuto.", exc_info=True)


def list_ticket_attachments(session: Session, ticket_id: int) -> list[Attachment]:
    """Elenca gli allegati del ticket, ordinati dal meno recente al più recente."""

    return list(
        session.scalars(
            select(Attachment)
            .where(
                Attachment.context_type == AttachmentContextType.TICKET,
                Attachment.context_id == ticket_id,
            )
            .order_by(Attachment.created_at, Attachment.id)
        ).all()
    )


def get_visible_attachment(session: Session, current_user: User, attachment_id: int) -> Attachment:
    """Restituisce un allegato solo dopo il controllo del relativo ticket."""

    attachment = session.get(Attachment, attachment_id)
    if attachment is None or attachment.context_type != AttachmentContextType.TICKET:
        raise AttachmentNotFoundError
    if get_visible_ticket(session, current_user, attachment.context_id) is None:
        raise AttachmentNotFoundError
    return attachment


def attachment_file_path(attachment: Attachment, storage_directory: Path) -> Path:
    """Risolve il file e verifica dimensione e impronta prima di servirlo."""

    path = _safe_stored_path(storage_directory, attachment.storage_filename)
    try:
        if not path.is_file() or path.stat().st_size != attachment.size_bytes:
            raise AttachmentStorageError("Il file allegato non è disponibile.")
        checksum = hashlib.sha256()
        with path.open("rb") as stored_file:
            while chunk := stored_file.read(READ_CHUNK_SIZE):
                checksum.update(chunk)
    except OSError as error:
        raise AttachmentStorageError("Il file allegato non è disponibile.") from error
    if checksum.hexdigest() != attachment.checksum_sha256:
        LOGGER.error("Controllo di integrità fallito per un allegato privato.")
        raise AttachmentStorageError("Il file allegato non è disponibile.")
    return path


def delete_context_attachments(
    session: Session,
    context: AttachmentContext,
    storage_directory: Path,
) -> tuple[int, int]:
    """Rimuove prima i file e conserva i metadati finché la pulizia non riesce."""

    attachments = list(
        session.scalars(
            select(Attachment).where(
                Attachment.context_type == context.type,
                Attachment.context_id == context.id,
            )
        ).all()
    )
    failures = 0
    for attachment in attachments:
        try:
            path = _safe_stored_path(storage_directory, attachment.storage_filename)
            path.unlink(missing_ok=True)
        except (AttachmentStorageError, OSError):
            failures += 1
    if failures:
        LOGGER.error(
            "Cancellazione allegati rinviata: %s file non rimossi; metadati conservati.",
            failures,
        )
        return 0, failures

    try:
        for attachment in attachments:
            session.delete(attachment)
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise AttachmentPersistenceError(
            "Non siamo riusciti a eliminare gli allegati del contesto."
        ) from error
    return len(attachments), 0
