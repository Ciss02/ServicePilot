"""Verifiche dell'indicizzazione e della ricerca semantica locale."""

import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.contracts import EmbeddingModel, EmbeddingUnavailableError
from app.db import (
    KnowledgeDocument,
    KnowledgeSegment,
    User,
    build_engine,
    create_database,
)
from app.domain.vocabulary import Role
from app.knowledge import (
    INDEX_FAILED,
    INDEX_PENDING,
    INDEX_READY,
    KnowledgeSearchError,
    KnowledgeSearchValidationError,
    index_knowledge_document,
    search_knowledge,
)


class KeywordEmbeddingModel:
    """Vettori piccoli e deterministici per dimostrare l'ordine dei risultati."""

    model_name = "embedding-fittizio-v1"
    dimensions = 3

    @staticmethod
    def _vector(text: str) -> list[float]:
        normalized = text.casefold()
        if "vpn" in normalized or "connessione remota" in normalized:
            return [1.0, 0.0, 0.0]
        if "account" in normalized or "password" in normalized:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class UnavailableEmbeddingModel(KeywordEmbeddingModel):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        del texts
        raise EmbeddingUnavailableError("provider disattivato")

    def embed_query(self, text: str) -> list[float]:
        del text
        raise EmbeddingUnavailableError("provider disattivato")


class InvalidEmbeddingModel(KeywordEmbeddingModel):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _text in texts]


@pytest.fixture
def indexing_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'indexing-test.db'}")
    create_database(engine)
    with Session(engine) as session:
        admin = User(
            email="admin.indexing@example.test",
            display_name="Admin Indicizzazione Demo",
            role=Role.ADMIN,
        )
        session.add(admin)
        session.flush()
        vpn_document = KnowledgeDocument(
            original_filename="procedura-vpn-demo.md",
            storage_filename="vpn-demo.md",
            content_type="text/markdown",
            size_bytes=120,
            checksum_sha256="a" * 64,
            uploaded_by_user_id=admin.id,
            extraction_status="ready",
        )
        account_document = KnowledgeDocument(
            original_filename="procedura-account-demo.md",
            storage_filename="account-demo.md",
            content_type="text/markdown",
            size_bytes=120,
            checksum_sha256="b" * 64,
            uploaded_by_user_id=admin.id,
            extraction_status="ready",
        )
        session.add_all([vpn_document, account_document])
        session.flush()
        session.add_all(
            [
                KnowledgeSegment(
                    document_id=vpn_document.id,
                    position=0,
                    source_section="VPN > Riconnessione",
                    content="Chiudere e riaprire il client VPN fittizio.",
                    character_count=47,
                ),
                KnowledgeSegment(
                    document_id=account_document.id,
                    position=0,
                    source_section="Account > Sblocco",
                    content="Avviare la procedura fittizia di sblocco account.",
                    character_count=50,
                ),
            ]
        )
        session.commit()
        yield session, vpn_document, account_document
    engine.dispose()


def test_indexing_stores_normalized_vectors_and_document_metadata(
    indexing_context,
) -> None:
    session, vpn_document, _ = indexing_context
    model: EmbeddingModel = KeywordEmbeddingModel()

    result = index_knowledge_document(session, vpn_document, model)
    segment = session.scalar(
        select(KnowledgeSegment).where(KnowledgeSegment.document_id == vpn_document.id)
    )

    assert result.status == INDEX_READY
    assert result.indexed_segments == 1
    assert vpn_document.index_status == INDEX_READY
    assert vpn_document.embedding_model == model.model_name
    assert vpn_document.embedding_dimensions == model.dimensions
    assert vpn_document.indexed_at is not None
    assert segment is not None
    assert json.loads(segment.embedding_json or "null") == [1.0, 0.0, 0.0]


def test_linked_question_finds_known_procedure_and_keeps_source(
    indexing_context,
) -> None:
    session, vpn_document, account_document = indexing_context
    model = KeywordEmbeddingModel()
    index_knowledge_document(session, vpn_document, model)
    index_knowledge_document(session, account_document, model)

    results = search_knowledge(
        session,
        model,
        "La connessione remota VPN cade dopo pochi minuti",
    )

    assert results[0].filename == "procedura-vpn-demo.md"
    assert results[0].source_section == "VPN > Riconnessione"
    assert "client VPN" in results[0].content
    assert results[0].score == 1.0
    assert results[0].document_id == vpn_document.id


def test_disabled_provider_leaves_document_ready_to_index(indexing_context) -> None:
    session, vpn_document, _ = indexing_context

    result = index_knowledge_document(
        session,
        vpn_document,
        UnavailableEmbeddingModel(),
    )

    assert result.status == INDEX_PENDING
    assert result.indexed_segments == 0
    assert vpn_document.index_status == INDEX_PENDING
    assert vpn_document.embedding_model is None


def test_invalid_vectors_fail_without_leaving_partial_index(indexing_context) -> None:
    session, vpn_document, _ = indexing_context
    index_knowledge_document(session, vpn_document, KeywordEmbeddingModel())

    result = index_knowledge_document(
        session,
        vpn_document,
        InvalidEmbeddingModel(),
    )
    segment = session.scalar(
        select(KnowledgeSegment).where(KnowledgeSegment.document_id == vpn_document.id)
    )

    assert result.status == INDEX_FAILED
    assert vpn_document.index_status == INDEX_FAILED
    assert vpn_document.embedding_model is None
    assert segment is not None
    assert segment.embedding_json is None


@pytest.mark.parametrize("query", ["", "  ", "ab", "x" * 501])
def test_search_rejects_queries_outside_the_safe_limits(
    indexing_context,
    query: str,
) -> None:
    session, _, _ = indexing_context

    with pytest.raises(KnowledgeSearchValidationError):
        search_knowledge(session, KeywordEmbeddingModel(), query)


def test_search_hides_provider_failure_behind_a_controlled_error(
    indexing_context,
) -> None:
    session, _, _ = indexing_context

    with pytest.raises(KnowledgeSearchError, match="non è disponibile"):
        search_knowledge(
            session,
            UnavailableEmbeddingModel(),
            "Problema VPN fittizio",
        )
