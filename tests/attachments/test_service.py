"""Verifiche di sicurezza, pulizia e autorizzazione degli allegati."""

from io import BytesIO

import pytest
from fastapi import UploadFile
from PIL import Image
from pypdf import PdfWriter
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

import app.attachments.service as attachment_service
from app.attachments import (
    MAX_CONTEXT_SIZE_BYTES,
    AttachmentContext,
    AttachmentNotFoundError,
    AttachmentPersistenceError,
    AttachmentValidationError,
    delete_context_attachments,
    get_visible_attachment,
    store_ticket_attachments,
)
from app.db import Attachment, Site, Ticket, User, build_engine, create_database
from app.domain.vocabulary import AttachmentContextType, Role


def make_upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    """Crea un upload browser fittizio senza accedere a file reali."""

    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def pdf_bytes() -> bytes:
    """Genera un PDF minimale ma valido per il parser reale."""

    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    return output.getvalue()


def jpeg_with_orientation() -> bytes:
    """Crea un JPEG con EXIF da rimuovere e orientare durante il salvataggio."""

    output = BytesIO()
    image = Image.new("RGB", (2, 5), color="blue")
    exif = Image.Exif()
    exif[274] = 6
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


@pytest.fixture
def attachment_context(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'attachments.db'}")
    create_database(engine)
    with Session(engine) as session:
        owner = User(
            email="owner.attachments@example.test",
            display_name="Owner Allegati Demo",
            role=Role.EMPLOYEE,
        )
        other_employee = User(
            email="other.attachments@example.test",
            display_name="Altro Dipendente Demo",
            role=Role.EMPLOYEE,
        )
        technician = User(
            email="technician.attachments@example.test",
            display_name="Tecnico Allegati Demo",
            role=Role.TECHNICIAN,
        )
        site = Site(code="ATTACHMENTS", name="Sede Allegati Demo")
        session.add_all([owner, other_employee, technician, site])
        session.flush()
        ticket = Ticket(
            title="Ticket allegati demo",
            description="Ticket fittizio per verificare l'archivio privato.",
            requester_id=owner.id,
            site_id=site.id,
            service="Archivio allegati",
            affected_users=1,
        )
        session.add(ticket)
        session.commit()
        yield session, owner, other_employee, technician, ticket, tmp_path / "attachments"
    engine.dispose()


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "stored_type"),
    [
        ("diagnostica.log", b"riga di log demo\n", "text/plain", "text/plain"),
        ("diagnostica.log", b"riga di log demo\n", "application/octet-stream", "text/plain"),
        ("procedura.pdf", pdf_bytes(), "application/pdf", "application/pdf"),
    ],
)
def test_valid_attachment_is_stored_with_private_random_name(
    attachment_context,
    filename: str,
    content: bytes,
    content_type: str,
    stored_type: str,
) -> None:
    session, owner, _, _, ticket, storage_directory = attachment_context

    attachment = store_ticket_attachments(
        session,
        [make_upload(f"C:/fake/path/{filename}", content, content_type)],
        ticket,
        owner,
        storage_directory,
    )[0]

    assert attachment.original_filename == filename
    assert attachment.storage_filename != filename
    assert attachment.content_type == stored_type
    assert len(attachment.checksum_sha256) == 64
    assert (storage_directory / attachment.storage_filename).is_file()


def test_jpeg_is_reoriented_and_saved_without_exif(attachment_context) -> None:
    session, owner, _, _, ticket, storage_directory = attachment_context

    attachment = store_ticket_attachments(
        session,
        [make_upload("foto.jpg", jpeg_with_orientation(), "image/jpeg")],
        ticket,
        owner,
        storage_directory,
    )[0]

    with Image.open(storage_directory / attachment.storage_filename) as image:
        assert image.size == (5, 2)
        assert not image.getexif()


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("foto.png", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "image/png"),
        ("procedura.pdf", b"%PDF-1.7\nnot a valid document", "application/pdf"),
        ("errore.txt", b"<html><body>non e un log</body></html>", "text/plain"),
        ("errore.log", b"\xff\xfe\x00\x01", "text/plain"),
        ("comando.exe", b"MZ", "application/octet-stream"),
    ],
)
def test_disguised_or_unsupported_attachment_is_rejected_without_files(
    attachment_context,
    filename: str,
    content: bytes,
    content_type: str,
) -> None:
    session, owner, _, _, ticket, storage_directory = attachment_context

    with pytest.raises(AttachmentValidationError):
        store_ticket_attachments(
            session,
            [make_upload(filename, content, content_type)],
            ticket,
            owner,
            storage_directory,
        )

    assert session.scalar(select(func.count()).select_from(Attachment)) == 0
    assert not storage_directory.exists()


def test_limits_are_rechecked_for_request_and_context(attachment_context) -> None:
    session, owner, _, _, ticket, storage_directory = attachment_context
    many_uploads = [make_upload(f"file-{number}.txt", b"demo", "text/plain") for number in range(6)]

    with pytest.raises(AttachmentValidationError, match="da 1 a 5"):
        store_ticket_attachments(session, many_uploads, ticket, owner, storage_directory)

    session.add(
        Attachment(
            context_type=AttachmentContextType.TICKET,
            context_id=ticket.id,
            owner_user_id=owner.id,
            original_filename="precedente.log",
            storage_filename="precedente.log",
            content_type="text/plain",
            size_bytes=MAX_CONTEXT_SIZE_BYTES,
            checksum_sha256="a" * 64,
        )
    )
    session.commit()

    with pytest.raises(AttachmentValidationError, match="100 MB"):
        store_ticket_attachments(
            session,
            [make_upload("nuovo.log", b"nuovo", "text/plain")],
            ticket,
            owner,
            storage_directory,
        )

    assert not storage_directory.exists()


def test_disk_error_removes_temporary_and_final_files(attachment_context, monkeypatch) -> None:
    session, owner, _, _, ticket, storage_directory = attachment_context

    def fail_replace(*_args, **_kwargs) -> None:
        raise OSError("disco demo non disponibile")

    monkeypatch.setattr(attachment_service.os, "replace", fail_replace)

    with pytest.raises(AttachmentPersistenceError):
        store_ticket_attachments(
            session,
            [make_upload("diagnostica.log", b"riga demo", "text/plain")],
            ticket,
            owner,
            storage_directory,
        )

    assert session.scalar(select(func.count()).select_from(Attachment)) == 0
    assert not list(storage_directory.iterdir())


def test_visibility_follows_ticket_authorization(attachment_context) -> None:
    session, owner, other_employee, technician, ticket, storage_directory = attachment_context
    attachment = store_ticket_attachments(
        session,
        [make_upload("diagnostica.log", b"riga demo", "text/plain")],
        ticket,
        owner,
        storage_directory,
    )[0]

    assert get_visible_attachment(session, owner, attachment.id).id == attachment.id
    assert get_visible_attachment(session, technician, attachment.id).id == attachment.id
    with pytest.raises(AttachmentNotFoundError):
        get_visible_attachment(session, other_employee, attachment.id)


def test_context_deletion_removes_metadata_and_file(attachment_context) -> None:
    session, owner, _, _, ticket, storage_directory = attachment_context
    attachment = store_ticket_attachments(
        session,
        [make_upload("diagnostica.log", b"riga demo", "text/plain")],
        ticket,
        owner,
        storage_directory,
    )[0]
    stored_path = storage_directory / attachment.storage_filename

    deleted, failures = delete_context_attachments(
        session,
        AttachmentContext(AttachmentContextType.TICKET, ticket.id),
        storage_directory,
    )

    assert (deleted, failures) == (1, 0)
    assert not stored_path.exists()
    assert session.scalar(select(func.count()).select_from(Attachment)) == 0
