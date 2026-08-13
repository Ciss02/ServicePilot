"""Archivio privato per gli allegati dei flussi operativi."""

from app.attachments.configuration import (
    ATTACHMENT_STORAGE_DIRECTORY_ENV,
    get_attachment_storage_directory,
)
from app.attachments.service import (
    MAX_ATTACHMENT_SIZE_BYTES,
    MAX_ATTACHMENTS_PER_REQUEST,
    MAX_CONTEXT_SIZE_BYTES,
    AttachmentContext,
    AttachmentNotFoundError,
    AttachmentPersistenceError,
    AttachmentStorageError,
    AttachmentValidationError,
    attachment_file_path,
    delete_context_attachments,
    get_visible_attachment,
    list_ticket_attachments,
    store_ticket_attachments,
)

__all__ = [
    "AttachmentContext",
    "ATTACHMENT_STORAGE_DIRECTORY_ENV",
    "AttachmentNotFoundError",
    "AttachmentPersistenceError",
    "AttachmentStorageError",
    "AttachmentValidationError",
    "attachment_file_path",
    "MAX_ATTACHMENTS_PER_REQUEST",
    "MAX_ATTACHMENT_SIZE_BYTES",
    "MAX_CONTEXT_SIZE_BYTES",
    "delete_context_attachments",
    "get_attachment_storage_directory",
    "get_visible_attachment",
    "list_ticket_attachments",
    "store_ticket_attachments",
]
