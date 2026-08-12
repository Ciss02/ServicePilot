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
from app.knowledge.extraction import (
    EXTRACTION_FAILED,
    EXTRACTION_PENDING,
    EXTRACTION_READY,
    MAX_SEGMENT_CHARACTERS,
    ExtractionResult,
    KnowledgeDocumentProcessingError,
    build_segment_drafts,
    process_knowledge_document,
)

__all__ = [
    "ALLOWED_DOCUMENT_EXTENSIONS",
    "DEFAULT_KNOWLEDGE_STORAGE_DIRECTORY",
    "KNOWLEDGE_STORAGE_DIRECTORY_ENV",
    "MAX_DOCUMENT_SIZE_BYTES",
    "MAX_SEGMENT_CHARACTERS",
    "EXTRACTION_FAILED",
    "EXTRACTION_PENDING",
    "EXTRACTION_READY",
    "ExtractionResult",
    "KnowledgeDocumentPersistenceError",
    "KnowledgeDocumentProcessingError",
    "KnowledgeDocumentValidationError",
    "get_knowledge_storage_directory",
    "build_segment_drafts",
    "process_knowledge_document",
    "store_knowledge_document",
]
