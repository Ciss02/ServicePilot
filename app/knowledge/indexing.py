"""Indicizzazione vettoriale e ricerca dei segmenti della knowledge base."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite, sqrt

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.contracts import (
    AIModelError,
    EmbeddingModel,
    EmbeddingUnavailableError,
)
from app.db.models import KnowledgeDocument, KnowledgeSegment
from app.knowledge.extraction import EXTRACTION_READY


INDEX_PENDING = "pending"
INDEX_READY = "ready"
INDEX_FAILED = "failed"
MIN_SEARCH_QUERY_CHARACTERS = 3
MAX_SEARCH_QUERY_CHARACTERS = 500
DEFAULT_SEARCH_LIMIT = 3
MAX_SEARCH_LIMIT = 10


class KnowledgeIndexingError(RuntimeError):
    """L'indice non ha potuto essere salvato senza risultati parziali."""


class KnowledgeSearchError(RuntimeError):
    """La ricerca non ha potuto produrre risultati affidabili."""


class KnowledgeSearchValidationError(ValueError):
    """La domanda non rispetta i limiti del laboratorio di ricerca."""


@dataclass(frozen=True)
class IndexingResult:
    """Esito sintetico dell'indicizzazione di un documento."""

    status: str
    indexed_segments: int


@dataclass(frozen=True)
class KnowledgeSearchResult:
    """Passaggio pertinente con fonte e punteggio di somiglianza."""

    segment_id: int
    document_id: int
    filename: str
    source_section: str
    content: str
    score: float


def _normalize_vector(values: object, dimensions: int) -> list[float]:
    if not isinstance(values, list) or len(values) != dimensions:
        raise ValueError("Il vettore non ha la dimensione configurata.")
    try:
        vector = [float(value) for value in values]
    except (TypeError, ValueError) as error:
        raise ValueError("Il vettore contiene valori non numerici.") from error
    if not all(isfinite(value) for value in vector):
        raise ValueError("Il vettore contiene valori numerici non validi.")
    norm = sqrt(sum(value * value for value in vector))
    if norm == 0:
        raise ValueError("Il vettore non contiene informazioni utilizzabili.")
    return [value / norm for value in vector]


def _clear_segment_embeddings(
    session: Session,
    document_id: int,
) -> None:
    segments = session.scalars(
        select(KnowledgeSegment).where(
            KnowledgeSegment.document_id == document_id
        )
    ).all()
    for segment in segments:
        segment.embedding_json = None


def _save_index_state(
    session: Session,
    document: KnowledgeDocument,
    *,
    status: str,
    error_message: str | None,
) -> None:
    try:
        _clear_segment_embeddings(session, document.id)
        document.index_status = status
        document.index_error = error_message[:300] if error_message else None
        document.embedding_model = None
        document.embedding_dimensions = None
        document.indexed_at = None
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise KnowledgeIndexingError(
            "Lo stato dell'indice non è stato salvato correttamente."
        ) from error


def index_knowledge_document(
    session: Session,
    document: KnowledgeDocument,
    embedding_model: EmbeddingModel,
) -> IndexingResult:
    """Genera e salva tutti i vettori del documento in un'unica operazione."""

    if document.extraction_status != EXTRACTION_READY:
        raise ValueError("Il documento deve essere estratto prima dell'indicizzazione.")

    segments = list(
        session.scalars(
            select(KnowledgeSegment)
            .where(KnowledgeSegment.document_id == document.id)
            .order_by(KnowledgeSegment.position)
        ).all()
    )
    if not segments:
        _save_index_state(
            session,
            document,
            status=INDEX_FAILED,
            error_message="Il documento non contiene segmenti da indicizzare.",
        )
        return IndexingResult(status=INDEX_FAILED, indexed_segments=0)

    try:
        raw_vectors = embedding_model.embed_documents(
            [segment.content for segment in segments]
        )
    except EmbeddingUnavailableError:
        _save_index_state(
            session,
            document,
            status=INDEX_PENDING,
            error_message=None,
        )
        return IndexingResult(status=INDEX_PENDING, indexed_segments=0)
    except AIModelError:
        _save_index_state(
            session,
            document,
            status=INDEX_FAILED,
            error_message="Il provider non ha generato un indice valido.",
        )
        return IndexingResult(status=INDEX_FAILED, indexed_segments=0)

    if len(raw_vectors) != len(segments):
        _save_index_state(
            session,
            document,
            status=INDEX_FAILED,
            error_message="Il numero di vettori non corrisponde ai segmenti.",
        )
        return IndexingResult(status=INDEX_FAILED, indexed_segments=0)

    try:
        vectors = [
            _normalize_vector(vector, embedding_model.dimensions)
            for vector in raw_vectors
        ]
    except ValueError as error:
        _save_index_state(
            session,
            document,
            status=INDEX_FAILED,
            error_message=str(error),
        )
        return IndexingResult(status=INDEX_FAILED, indexed_segments=0)

    try:
        for segment, vector in zip(segments, vectors, strict=True):
            segment.embedding_json = json.dumps(vector, separators=(",", ":"))
        document.index_status = INDEX_READY
        document.index_error = None
        document.embedding_model = embedding_model.model_name
        document.embedding_dimensions = embedding_model.dimensions
        document.indexed_at = datetime.now(UTC)
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise KnowledgeIndexingError(
            "Non siamo riusciti a salvare l'indice completo del documento."
        ) from error

    return IndexingResult(status=INDEX_READY, indexed_segments=len(segments))


def search_knowledge(
    session: Session,
    embedding_model: EmbeddingModel,
    query: str,
    *,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> list[KnowledgeSearchResult]:
    """Recupera i segmenti più simili mantenendo documento e sezione."""

    normalized_query = " ".join(query.split())
    if not (
        MIN_SEARCH_QUERY_CHARACTERS
        <= len(normalized_query)
        <= MAX_SEARCH_QUERY_CHARACTERS
    ):
        raise KnowledgeSearchValidationError(
            "Scrivi una domanda compresa tra 3 e 500 caratteri."
        )
    if not 1 <= limit <= MAX_SEARCH_LIMIT:
        raise ValueError(
            "Il limite dei risultati deve essere compreso tra "
            f"1 e {MAX_SEARCH_LIMIT}."
        )

    try:
        query_vector = _normalize_vector(
            embedding_model.embed_query(normalized_query),
            embedding_model.dimensions,
        )
    except AIModelError as error:
        raise KnowledgeSearchError(
            "La ricerca semantica non è disponibile in questo momento."
        ) from error
    except ValueError as error:
        raise KnowledgeSearchError(
            "Il provider ha restituito una domanda non confrontabile."
        ) from error

    rows = session.execute(
        select(KnowledgeSegment, KnowledgeDocument)
        .join(
            KnowledgeDocument,
            KnowledgeDocument.id == KnowledgeSegment.document_id,
        )
        .where(
            KnowledgeDocument.index_status == INDEX_READY,
            KnowledgeDocument.embedding_model == embedding_model.model_name,
            KnowledgeDocument.embedding_dimensions == embedding_model.dimensions,
            KnowledgeSegment.embedding_json.is_not(None),
        )
    ).all()

    results: list[KnowledgeSearchResult] = []
    for segment, document in rows:
        try:
            stored_vector = _normalize_vector(
                json.loads(segment.embedding_json or "null"),
                embedding_model.dimensions,
            )
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
        score = sum(
            query_value * segment_value
            for query_value, segment_value in zip(
                query_vector,
                stored_vector,
                strict=True,
            )
        )
        results.append(
            KnowledgeSearchResult(
                segment_id=segment.id,
                document_id=document.id,
                filename=document.original_filename,
                source_section=segment.source_section,
                content=segment.content,
                score=score,
            )
        )

    return sorted(results, key=lambda result: (-result.score, result.segment_id))[:limit]
