"""Estrazione locale e segmentazione dei documenti della knowledge base."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import KnowledgeDocument, KnowledgeSegment


MAX_SEGMENT_CHARACTERS = 1200
SEGMENT_OVERLAP_CHARACTERS = 150
EXTRACTION_PENDING = "pending"
EXTRACTION_READY = "ready"
EXTRACTION_FAILED = "failed"

_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


class KnowledgeDocumentProcessingError(RuntimeError):
    """Il documento esiste, ma il risultato non ha potuto essere salvato."""


@dataclass(frozen=True)
class SourceText:
    """Testo estratto insieme al riferimento leggibile della fonte."""

    source_section: str
    content: str


@dataclass(frozen=True)
class SegmentDraft:
    """Segmento pronto per essere conservato nel database."""

    position: int
    source_section: str
    content: str


@dataclass(frozen=True)
class ExtractionResult:
    """Esito sintetico mostrabile dall'interfaccia."""

    status: str
    segment_count: int


def _normalize_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _markdown_sources(text: str) -> list[SourceText]:
    """Usa i titoli Markdown come percorso di sezione, ignorandoli nei blocchi codice."""

    sections: list[SourceText] = []
    heading_path: list[str] = []
    current_lines: list[str] = []
    current_source = "Introduzione"
    fence_marker: str | None = None

    def save_current_section() -> None:
        content = _normalize_text("\n".join(current_lines))
        if content:
            sections.append(SourceText(current_source, content))

    for line in text.splitlines():
        stripped = line.strip()
        if fence_marker is not None:
            current_lines.append(line)
            if stripped.startswith(fence_marker):
                fence_marker = None
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence_marker = stripped[:3]
            current_lines.append(line)
            continue

        heading = _MARKDOWN_HEADING.match(stripped)
        if heading is None:
            current_lines.append(line)
            continue

        save_current_section()
        current_lines = []
        level = len(heading.group(1))
        title = heading.group(2).strip()
        heading_path = heading_path[: level - 1]
        heading_path.append(title)
        current_source = " > ".join(heading_path)

    save_current_section()
    return sections


def _pdf_sources(path: Path) -> list[SourceText]:
    """Estrae il testo selezionabile e usa la pagina come riferimento certo."""

    reader = PdfReader(path, strict=False)
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError("Il PDF è protetto da password.")

    sources: list[SourceText] = []
    for page_number, page in enumerate(reader.pages, start=1):
        content = _normalize_text(page.extract_text() or "")
        if content:
            sources.append(SourceText(f"Pagina {page_number}", content))
    return sources


def _split_text(text: str) -> list[str]:
    """Crea blocchi sovrapposti senza superare la dimensione massima."""

    compact_text = re.sub(r"\s+", " ", text).strip()
    if not compact_text:
        return []
    if len(compact_text) <= MAX_SEGMENT_CHARACTERS:
        return [compact_text]

    chunks: list[str] = []
    start = 0
    while start < len(compact_text):
        end = min(start + MAX_SEGMENT_CHARACTERS, len(compact_text))
        if end < len(compact_text):
            boundary = compact_text.rfind(" ", start + MAX_SEGMENT_CHARACTERS // 2, end)
            if boundary > start:
                end = boundary
        chunk = compact_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(compact_text):
            break
        next_start = max(end - SEGMENT_OVERLAP_CHARACTERS, start + 1)
        next_space = compact_text.find(" ", next_start)
        start = next_space + 1 if next_space != -1 and next_space < end else next_start
    return chunks


def build_segment_drafts(document: KnowledgeDocument, path: Path) -> list[SegmentDraft]:
    """Estrae il formato noto e assegna una posizione stabile a ogni segmento."""

    if document.content_type == "application/pdf":
        sources = _pdf_sources(path)
    elif document.content_type == "text/markdown":
        sources = _markdown_sources(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Il formato del documento non è supportato per l'estrazione.")

    drafts: list[SegmentDraft] = []
    for source in sources:
        for content in _split_text(source.content):
            drafts.append(
                SegmentDraft(
                    position=len(drafts),
                    source_section=source.source_section[:255],
                    content=content,
                )
            )
    return drafts


def _save_failed_result(
    session: Session,
    document: KnowledgeDocument,
    message: str,
) -> ExtractionResult:
    try:
        session.execute(
            delete(KnowledgeSegment).where(
                KnowledgeSegment.document_id == document.id
            )
        )
        document.extraction_status = EXTRACTION_FAILED
        document.extraction_error = message[:300]
        document.index_status = "failed"
        document.index_error = "Il documento non contiene segmenti da indicizzare."
        document.embedding_model = None
        document.embedding_dimensions = None
        document.indexed_at = None
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise KnowledgeDocumentProcessingError(
            "Il documento è stato conservato, ma l'estrazione non è stata registrata."
        ) from error
    return ExtractionResult(status=EXTRACTION_FAILED, segment_count=0)


def process_knowledge_document(
    session: Session,
    document: KnowledgeDocument,
    storage_directory: Path,
) -> ExtractionResult:
    """Estrae e sostituisce tutti i segmenti senza lasciare risultati parziali."""

    path = storage_directory / document.storage_filename
    try:
        drafts = build_segment_drafts(document, path)
    except (OSError, UnicodeError, ValueError) as error:
        return _save_failed_result(session, document, str(error))
    except Exception:
        return _save_failed_result(
            session,
            document,
            "Il PDF non contiene testo estraibile in un formato riconoscibile.",
        )

    if not drafts:
        return _save_failed_result(
            session,
            document,
            "Il documento non contiene testo selezionabile da segmentare.",
        )

    try:
        session.execute(
            delete(KnowledgeSegment).where(
                KnowledgeSegment.document_id == document.id
            )
        )
        session.add_all(
            [
                KnowledgeSegment(
                    document_id=document.id,
                    position=draft.position,
                    source_section=draft.source_section,
                    content=draft.content,
                    character_count=len(draft.content),
                )
                for draft in drafts
            ]
        )
        document.extraction_status = EXTRACTION_READY
        document.extraction_error = None
        document.index_status = "pending"
        document.index_error = None
        document.embedding_model = None
        document.embedding_dimensions = None
        document.indexed_at = None
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise KnowledgeDocumentProcessingError(
            "Il documento è stato conservato, ma i segmenti non sono stati salvati."
        ) from error

    return ExtractionResult(status=EXTRACTION_READY, segment_count=len(drafts))
