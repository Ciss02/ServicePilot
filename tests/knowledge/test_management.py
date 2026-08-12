"""Verifica eliminazione sicura di una fonte e dei dati da essa derivati."""

from io import BytesIO

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

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
    delete_knowledge_document,
    process_knowledge_document,
    store_knowledge_document,
)


def test_delete_document_invalidates_cited_solution_and_removes_file(tmp_path) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / 'delete-document.db'}")
    create_database(engine)
    storage_directory = tmp_path / "knowledge"
    with Session(engine) as session:
        admin = User(
            email="admin.delete@example.test",
            display_name="Admin Eliminazione Demo",
            role=Role.ADMIN,
        )
        requester = User(
            email="employee.delete@example.test",
            display_name="Dipendente Eliminazione Demo",
            role=Role.EMPLOYEE,
        )
        site = Site(code="DELETE-DEMO", name="Sede Eliminazione Demo")
        session.add_all([admin, requester, site])
        session.flush()
        ticket = Ticket(
            title="Ticket demo con fonte",
            description="Problema fittizio collegato a una procedura.",
            requester_id=requester.id,
            site_id=site.id,
            service="Servizio demo",
            affected_users=1,
            ai_suggested_solution="Suggerimento fittizio da invalidare.",
            ai_solution_status="generated",
        )
        session.add(ticket)
        session.commit()
        document = store_knowledge_document(
            session,
            UploadFile(
                filename="fonte-demo.md",
                file=BytesIO(b"# Fonte demo\n\nPassaggio tecnico fittizio."),
                headers={"content-type": "text/markdown"},
            ),
            uploaded_by=admin,
            storage_directory=storage_directory,
        )
        process_knowledge_document(session, document, storage_directory)
        segment = session.scalar(
            select(KnowledgeSegment).where(KnowledgeSegment.document_id == document.id)
        )
        session.add(
            TicketSolutionSource(
                ticket_id=ticket.id,
                segment_id=segment.id,
                rank=1,
                similarity_score=1.0,
            )
        )
        session.commit()
        stored_path = storage_directory / document.storage_filename

        result = delete_knowledge_document(
            session,
            document.id,
            storage_directory,
        )

        session.refresh(ticket)
        assert result.filename == "fonte-demo.md"
        assert result.stored_file_removed is True
        assert session.get(KnowledgeDocument, document.id) is None
        assert session.scalars(select(KnowledgeSegment)).all() == []
        assert session.scalars(select(TicketSolutionSource)).all() == []
        assert ticket.ai_suggested_solution is None
        assert ticket.ai_solution_status == "pending"
        assert not stored_path.exists()
    engine.dispose()
