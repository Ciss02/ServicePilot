"""Caricamento e conservazione dei documenti della knowledge base."""

from app.knowledge.configuration import (
    DEFAULT_KNOWLEDGE_STORAGE_DIRECTORY,
    KNOWLEDGE_STORAGE_DIRECTORY_ENV,
    get_knowledge_storage_directory,
)
from app.knowledge.uploads import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    MAX_DOCUMENT_SIZE_BYTES,
    KnowledgeDocumentPersistenceError,
    KnowledgeDocumentValidationError,
    store_knowledge_document,
)

__all__ = [
    "ALLOWED_DOCUMENT_EXTENSIONS",
    "DEFAULT_KNOWLEDGE_STORAGE_DIRECTORY",
    "KNOWLEDGE_STORAGE_DIRECTORY_ENV",
    "MAX_DOCUMENT_SIZE_BYTES",
    "KnowledgeDocumentPersistenceError",
    "KnowledgeDocumentValidationError",
    "get_knowledge_storage_directory",
    "store_knowledge_document",
]
