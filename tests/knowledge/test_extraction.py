"""Verifiche dell'estrazione e dei riferimenti alla fonte."""

from io import BytesIO

import pytest
from fastapi import UploadFile
from pypdf import PageObject, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import (
    KnowledgeSegment,
    User,
    build_engine,
    create_database,
)
from app.domain.vocabulary import Role
from app.knowledge import (
    EXTRACTION_FAILED,
    EXTRACTION_READY,
    MAX_SEGMENT_CHARACTERS,
    process_knowledge_document,
    store_knowledge_document,
)


def make_upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers={"content-type": content_type},
    )


def make_text_pdf(*page_texts: str) -> bytes:
    """Crea un piccolo PDF fittizio con testo selezionabile, senza file esterni."""

    writer = PdfWriter()
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)

    for page_text in page_texts:
        page = PageObject.create_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): font_reference}
                )
            }
        )
        stream = DecodedStreamObject()
        escaped_text = (
            page_text.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        stream.set_data(
            f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode("ascii")
        )
        page[NameObject("/Contents")] = writer._add_object(stream)
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def extraction_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'extraction-test.db'}")
    create_database(engine)
    storage_directory = tmp_path / "knowledge"
    with Session(engine) as session:
        admin = User(
            email="admin.extraction@example.test",
            display_name="Admin Estrazione Demo",
            role=Role.ADMIN,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        yield session, admin, storage_directory
    engine.dispose()


def test_markdown_segments_keep_document_and_heading_path(extraction_context) -> None:
    session, admin, storage_directory = extraction_context
    content = (
        "Contesto generale fittizio.\n\n"
        "# Wi-Fi demo\n\nControllare il segnale della rete demo.\n\n"
        "## Verifica finale\n\nConfermare la connessione di prova.\n"
    ).encode()
    document = store_knowledge_document(
        session,
        make_upload("wifi-demo.md", content, "text/markdown"),
        uploaded_by=admin,
        storage_directory=storage_directory,
    )

    result = process_knowledge_document(session, document, storage_directory)
    segments = list(
        session.scalars(
            select(KnowledgeSegment).order_by(KnowledgeSegment.position)
        ).all()
    )

    assert result.status == EXTRACTION_READY
    assert result.segment_count == 3
    assert document.extraction_status == EXTRACTION_READY
    assert [segment.source_section for segment in segments] == [
        "Introduzione",
        "Wi-Fi demo",
        "Wi-Fi demo > Verifica finale",
    ]
    assert all(segment.document_id == document.id for segment in segments)
    assert [segment.position for segment in segments] == [0, 1, 2]
    assert all(segment.character_count == len(segment.content) for segment in segments)


def test_long_section_is_split_without_losing_its_source(extraction_context) -> None:
    session, admin, storage_directory = extraction_context
    long_text = "# Procedura estesa\n\n" + ("passaggio fittizio controllato " * 160)
    document = store_knowledge_document(
        session,
        make_upload("procedura-estesa.md", long_text.encode(), "text/markdown"),
        uploaded_by=admin,
        storage_directory=storage_directory,
    )

    result = process_knowledge_document(session, document, storage_directory)
    segments = list(
        session.scalars(
            select(KnowledgeSegment).order_by(KnowledgeSegment.position)
        ).all()
    )

    assert result.segment_count > 1
    assert all(len(segment.content) <= MAX_SEGMENT_CHARACTERS for segment in segments)
    assert {segment.source_section for segment in segments} == {"Procedura estesa"}
    assert [segment.position for segment in segments] == list(range(len(segments)))


def test_pdf_segments_use_page_number_as_source(extraction_context) -> None:
    session, admin, storage_directory = extraction_context
    document = store_knowledge_document(
        session,
        make_upload(
            "vpn-demo.pdf",
            make_text_pdf(
                "Procedura VPN fittizia pagina uno",
                "Verifica VPN fittizia pagina due",
            ),
            "application/pdf",
        ),
        uploaded_by=admin,
        storage_directory=storage_directory,
    )

    result = process_knowledge_document(session, document, storage_directory)
    segments = list(
        session.scalars(
            select(KnowledgeSegment).order_by(KnowledgeSegment.position)
        ).all()
    )

    assert result.status == EXTRACTION_READY
    assert [segment.source_section for segment in segments] == [
        "Pagina 1",
        "Pagina 2",
    ]
    assert "Procedura VPN fittizia" in segments[0].content
    assert "Verifica VPN fittizia" in segments[1].content


def test_document_without_readable_text_is_marked_without_partial_segments(
    extraction_context,
) -> None:
    session, admin, storage_directory = extraction_context
    document = store_knowledge_document(
        session,
        make_upload("solo-titolo.md", b"# Solo titolo\n", "text/markdown"),
        uploaded_by=admin,
        storage_directory=storage_directory,
    )

    result = process_knowledge_document(session, document, storage_directory)

    assert result.status == EXTRACTION_FAILED
    assert result.segment_count == 0
    assert document.extraction_status == EXTRACTION_FAILED
    assert document.extraction_error is not None
    assert session.scalars(select(KnowledgeSegment)).all() == []


def test_processing_same_document_replaces_segments_instead_of_duplicating_them(
    extraction_context,
) -> None:
    session, admin, storage_directory = extraction_context
    document = store_knowledge_document(
        session,
        make_upload(
            "account-demo.md",
            b"# Account demo\n\nSbloccare l'account fittizio.\n",
            "text/markdown",
        ),
        uploaded_by=admin,
        storage_directory=storage_directory,
    )

    first = process_knowledge_document(session, document, storage_directory)
    second = process_knowledge_document(session, document, storage_directory)
    segments = session.scalars(select(KnowledgeSegment)).all()

    assert first.segment_count == second.segment_count == 1
    assert len(segments) == 1
    assert segments[0].document_id == document.id
