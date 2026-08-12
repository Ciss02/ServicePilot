"""Verifiche della generazione RAG e del collegamento alle fonti."""

import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import AIInvalidResponseError, AIUnavailableError
from app.db import (
    KnowledgeDocument,
    KnowledgeSegment,
    Site,
    Ticket,
    TicketSolutionSource,
    User,
    build_engine,
    create_database,
)
from app.domain.vocabulary import Role
from app.knowledge import (
    SOLUTION_GENERATED,
    SOLUTION_INVALID_RESPONSE,
    SOLUTION_UNAVAILABLE,
    generate_ticket_solution,
    list_ticket_solution_sources,
    suggest_sourced_solution,
)
from app.knowledge.indexing import KnowledgeSearchResult


class KeywordEmbeddingModel:
    model_name = "embedding-soluzioni-fittizio-v1"
    dimensions = 2

    def embed_query(self, text: str) -> list[float]:
        if "vpn" in text.casefold():
            return [1.0, 0.0]
        return [0.0, 1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]


class FirstSourceSolutionModel:
    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema,
        system_instruction: str | None = None,
    ):
        assert "esclusivamente" in (system_instruction or "")
        payload = json.loads(prompt)
        first_source = payload["retrieved_sources"][0]
        return response_schema.model_validate(
            {
                "solution": (
                    "Verificare la stabilità della VPN e ripetere la connessione "
                    "seguendo il passaggio indicato nella procedura."
                ),
                "cited_source_ids": [first_source["source_id"]],
            }
        )


class InventedSourceSolutionModel:
    def generate_structured(self, *, response_schema, **_kwargs):
        return response_schema.model_validate(
            {
                "solution": "Applicare una procedura fittizia non presente nelle fonti.",
                "cited_source_ids": [999_999],
            }
        )


class UnavailableSolutionModel:
    def generate_structured(self, **_kwargs):
        raise AIUnavailableError("timeout fittizio")


@pytest.fixture
def solution_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'solutions-test.db'}")
    create_database(engine)
    with Session(engine) as session:
        requester = User(
            email="richiedente.soluzioni@example.test",
            display_name="Richiedente Soluzioni Demo",
            role=Role.EMPLOYEE,
        )
        admin = User(
            email="admin.soluzioni@example.test",
            display_name="Admin Soluzioni Demo",
            role=Role.ADMIN,
        )
        site = Site(code="SOL-DEMO", name="Sede Soluzioni Demo")
        session.add_all([requester, admin, site])
        session.flush()
        ticket = Ticket(
            title="VPN demo instabile",
            description="La connessione VPN demo cade dopo pochi minuti.",
            requester_id=requester.id,
            site_id=site.id,
            service="Accesso remoto",
            affected_users=1,
        )
        document = KnowledgeDocument(
            original_filename="procedura-vpn-demo.md",
            storage_filename="procedura-vpn-demo-interna.md",
            content_type="text/markdown",
            size_bytes=200,
            checksum_sha256="a" * 64,
            extraction_status="ready",
            index_status="ready",
            embedding_model=KeywordEmbeddingModel.model_name,
            embedding_dimensions=KeywordEmbeddingModel.dimensions,
            uploaded_by_user_id=admin.id,
        )
        session.add_all([ticket, document])
        session.flush()
        vpn_segment = KnowledgeSegment(
            document_id=document.id,
            position=0,
            source_section="VPN > Nuovo tentativo",
            content=(
                "Disconnettere la VPN demo, attendere trenta secondi e riprovare "
                "verificando la stabilità del collegamento."
            ),
            character_count=112,
            embedding_json=json.dumps([1.0, 0.0]),
        )
        account_segment = KnowledgeSegment(
            document_id=document.id,
            position=1,
            source_section="Account > Sblocco",
            content="Verificare lo stato dell'account demo prima dello sblocco.",
            character_count=58,
            embedding_json=json.dumps([0.0, 1.0]),
        )
        session.add_all([vpn_segment, account_segment])
        session.commit()
        context = {
            "ticket_id": ticket.id,
            "vpn_segment_id": vpn_segment.id,
        }
    yield engine, context
    engine.dispose()


def test_generation_saves_solution_and_only_the_cited_passage(solution_context) -> None:
    engine, context = solution_context
    with Session(engine) as session:
        ticket = session.get(Ticket, context["ticket_id"])

        generate_ticket_solution(
            session,
            ticket,
            ai_model=FirstSourceSolutionModel(),
            embedding_model=KeywordEmbeddingModel(),
        )

        sources = list_ticket_solution_sources(session, ticket.id)
        stored_source = session.scalar(select(TicketSolutionSource))
        assert ticket.ai_solution_status == SOLUTION_GENERATED
        assert "Verificare la stabilità" in (ticket.ai_suggested_solution or "")
        assert ticket.ai_solution_generated_at is not None
        assert ticket.resolution is None
        assert stored_source.segment_id == context["vpn_segment_id"]
        assert len(sources) == 1
        assert sources[0].filename == "procedura-vpn-demo.md"
        assert sources[0].source_section == "VPN > Nuovo tentativo"
        assert "attendere trenta secondi" in sources[0].content


def test_model_cannot_cite_a_source_not_retrieved_by_backend(solution_context) -> None:
    engine, context = solution_context
    with Session(engine) as session:
        ticket = session.get(Ticket, context["ticket_id"])
        match = KnowledgeSearchResult(
            segment_id=context["vpn_segment_id"],
            document_id=1,
            filename="procedura-vpn-demo.md",
            source_section="VPN",
            content="Passaggio fittizio controllato per la VPN demo.",
            score=1.0,
        )

        with pytest.raises(AIInvalidResponseError, match="non recuperata"):
            suggest_sourced_solution(
                ticket,
                [match],
                ai_model=InventedSourceSolutionModel(),
            )


def test_invalid_citation_is_saved_as_controlled_failure(solution_context) -> None:
    engine, context = solution_context
    with Session(engine) as session:
        ticket = session.get(Ticket, context["ticket_id"])

        generate_ticket_solution(
            session,
            ticket,
            ai_model=InventedSourceSolutionModel(),
            embedding_model=KeywordEmbeddingModel(),
        )

        assert ticket.ai_solution_status == SOLUTION_INVALID_RESPONSE
        assert ticket.ai_suggested_solution is None
        assert session.scalar(select(TicketSolutionSource)) is None


def test_unavailable_ai_keeps_ticket_usable_without_sources(solution_context) -> None:
    engine, context = solution_context
    with Session(engine) as session:
        ticket = session.get(Ticket, context["ticket_id"])

        generate_ticket_solution(
            session,
            ticket,
            ai_model=UnavailableSolutionModel(),
            embedding_model=KeywordEmbeddingModel(),
        )

        assert ticket.ai_solution_status == SOLUTION_UNAVAILABLE
        assert ticket.ai_suggested_solution is None
        assert ticket.resolution is None
        assert session.scalar(select(TicketSolutionSource)) is None
