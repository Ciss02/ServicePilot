"""Verifiche del caricamento sicuro dei documenti."""

from io import BytesIO

import pytest
from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from app.db import KnowledgeDocument, User, build_engine, create_database
from app.domain.vocabulary import Role
from app.knowledge import (
    MAX_DOCUMENT_SIZE_BYTES,
    KnowledgeDocumentPersistenceError,
    KnowledgeDocumentValidationError,
    store_knowledge_document,
)


def make_upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


@pytest.fixture
def upload_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'knowledge-test.db'}")
    create_database(engine)
    storage_directory = tmp_path / "knowledge"
    with Session(engine) as session:
        admin = User(
            email="admin.knowledge@example.test",
            display_name="Admin Knowledge Demo",
            role=Role.ADMIN,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        yield session, admin, storage_directory
    engine.dispose()


@pytest.mark.parametrize(
    ("filename", "content", "declared_type", "stored_type", "stored_suffix"),
    [
        (
            "procedura-vpn.pdf",
            b"%PDF-1.7\nProcedura PDF fittizia\n%%EOF",
            "application/pdf",
            "application/pdf",
            ".pdf",
        ),
        (
            "procedura-vpn.md",
            b"# VPN demo\n\nProcedura fittizia per il test.\n",
            "text/markdown",
            "text/markdown",
            ".md",
        ),
    ],
)
def test_allowed_document_is_stored_with_safe_name_and_metadata(
    upload_context,
    filename: str,
    content: bytes,
    declared_type: str,
    stored_type: str,
    stored_suffix: str,
) -> None:
    session, admin, storage_directory = upload_context

    document = store_knowledge_document(
        session,
        make_upload(filename, content, declared_type),
        uploaded_by=admin,
        storage_directory=storage_directory,
    )

    assert document.original_filename == filename
    assert document.storage_filename != filename
    assert document.storage_filename.endswith(stored_suffix)
    assert document.content_type == stored_type
    assert document.size_bytes == len(content)
    assert len(document.checksum_sha256) == 64
    assert document.uploaded_by_user_id == admin.id
    assert (storage_directory / document.storage_filename).read_bytes() == content


def test_path_parts_from_browser_filename_are_not_used_for_storage(upload_context) -> None:
    session, admin, storage_directory = upload_context

    document = store_knowledge_document(
        session,
        make_upload(
            "../../procedure/demo.md",
            b"# Documento demo\n",
            "text/markdown",
        ),
        uploaded_by=admin,
        storage_directory=storage_directory,
    )

    assert document.original_filename == "demo.md"
    assert document.storage_filename != "demo.md"
    assert (storage_directory / document.storage_filename).is_file()


@pytest.mark.parametrize(
    ("filename", "content", "declared_type", "message"),
    [
        ("procedura.txt", b"testo", "text/plain", "Formato non ammesso"),
        (
            "procedura.pdf",
            b"non e un pdf",
            "application/pdf",
            "non contiene un documento PDF",
        ),
        (
            "procedura.pdf",
            b"%PDF-1.7\n%%EOF",
            "text/plain",
            "tipo dichiarato",
        ),
        (
            "procedura.md",
            b"\xff\xfe\x00\x01",
            "text/markdown",
            "testo UTF-8 valido",
        ),
        ("procedura.md", b"", "text/markdown", "documento è vuoto"),
    ],
)
def test_invalid_document_is_rejected_without_partial_changes(
    upload_context,
    filename: str,
    content: bytes,
    declared_type: str,
    message: str,
) -> None:
    session, admin, storage_directory = upload_context

    with pytest.raises(KnowledgeDocumentValidationError, match=message):
        store_knowledge_document(
            session,
            make_upload(filename, content, declared_type),
            uploaded_by=admin,
            storage_directory=storage_directory,
        )

    assert session.scalar(select(func.count()).select_from(KnowledgeDocument)) == 0
    assert not storage_directory.exists() or not list(storage_directory.iterdir())


def test_oversized_document_is_rejected_before_storage(upload_context) -> None:
    session, admin, storage_directory = upload_context
    content = b"#" + (b"a" * MAX_DOCUMENT_SIZE_BYTES)

    with pytest.raises(KnowledgeDocumentValidationError, match="supera il limite"):
        store_knowledge_document(
            session,
            make_upload("troppo-grande.md", content, "text/markdown"),
            uploaded_by=admin,
            storage_directory=storage_directory,
        )

    assert session.scalar(select(func.count()).select_from(KnowledgeDocument)) == 0
    assert not storage_directory.exists()


def test_database_failure_removes_the_already_validated_file(upload_context) -> None:
    session, _, storage_directory = upload_context
    missing_admin = User(
        id=999_999,
        email="admin.assente@example.test",
        display_name="Admin Assente Demo",
        role=Role.ADMIN,
    )

    with pytest.raises(KnowledgeDocumentPersistenceError):
        store_knowledge_document(
            session,
            make_upload(
                "procedura.md",
                b"# Documento senza autore persistente\n",
                "text/markdown",
            ),
            uploaded_by=missing_admin,
            storage_directory=storage_directory,
        )

    assert session.scalar(select(func.count()).select_from(KnowledgeDocument)) == 0
    assert list(storage_directory.iterdir()) == []
