"""Tabelle iniziali persistenti di ServicePilot."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy import event as sqlalchemy_event
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.vocabulary import (
    ActionStatus,
    ActionType,
    AuditActorType,
    AuditEventType,
    ClassificationReviewStatus,
    Impact,
    Priority,
    Role,
    TicketCategory,
    TicketStatus,
    Urgency,
)


def _enum_values(enum_class: type[StrEnum]) -> list[str]:
    """Conserva nel database i codici stabili, non i nomi Python."""

    return [member.value for member in enum_class]


def _enum_column(enum_class: type[StrEnum], name: str) -> Enum:
    """Crea un campo testuale limitato ai valori del vocabolario."""

    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=_enum_values,
    )


class User(Base):
    """Account fittizio che potrà accedere alla demo."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(_enum_column(Role, "role"), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class SupportGroup(Base):
    """Gruppo tecnico amministrabile usato per le nuove assegnazioni."""

    __tablename__ = "support_groups"
    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) BETWEEN 2 AND 100",
            name="ck_support_groups_name_length",
        ),
        CheckConstraint(
            "length(trim(description)) BETWEEN 2 AND 500",
            name="ck_support_groups_description_length",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class SupportGroupMembership(Base):
    """Appartenenza di un tecnico o amministratore a un gruppo di supporto."""

    __tablename__ = "support_group_memberships"

    support_group_id: Mapped[int] = mapped_column(
        ForeignKey("support_groups.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class AuthSession(Base):
    """Sessione autenticata; il codice originale resta soltanto nel browser."""

    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class Site(Base):
    """Sede fittizia alla quale appartengono utenti e ticket."""

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class KnowledgeDocument(Base):
    """Documento amministrativo conservato e preparato per la ricerca."""

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_knowledge_documents_size"),
        CheckConstraint(
            "extraction_status IN ('pending', 'ready', 'failed')",
            name="ck_knowledge_documents_extraction_status",
        ),
        CheckConstraint(
            "index_status IN ('pending', 'ready', 'failed')",
            name="ck_knowledge_documents_index_status",
        ),
        CheckConstraint(
            "embedding_dimensions IS NULL OR embedding_dimensions > 0",
            name="ck_knowledge_documents_embedding_dimensions",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_filename: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    extraction_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    extraction_error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    index_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    index_error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class KnowledgeSegment(Base):
    """Passaggio leggibile con il riferimento alla propria fonte."""

    __tablename__ = "knowledge_segments"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_knowledge_segments_position"),
        CheckConstraint("character_count > 0", name="ck_knowledge_segments_character_count"),
        UniqueConstraint("document_id", "position", name="ux_knowledge_segments_document_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    source_section: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class Ticket(Base):
    """Richiesta IT confermata e salvata dall'applicazione."""

    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(
            "affected_users BETWEEN 1 AND 10000",
            name="ck_tickets_affected_users",
        ),
        CheckConstraint(
            "ai_solution_status IN ('pending', 'generated', 'unavailable', 'invalid_response')",
            name="ck_tickets_ai_solution_status",
        ),
        Index("ux_tickets_creation_key", "creation_key", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_users: Mapped[int] = mapped_column(Integer, nullable=False)
    creation_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[TicketCategory | None] = mapped_column(
        _enum_column(TicketCategory, "ticket_category"), nullable=True
    )
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    impact: Mapped[Impact | None] = mapped_column(_enum_column(Impact, "impact"), nullable=True)
    urgency: Mapped[Urgency | None] = mapped_column(_enum_column(Urgency, "urgency"), nullable=True)
    priority: Mapped[Priority | None] = mapped_column(
        _enum_column(Priority, "priority"), nullable=True
    )
    assigned_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_review_status: Mapped[ClassificationReviewStatus] = mapped_column(
        _enum_column(ClassificationReviewStatus, "classification_review_status"),
        nullable=False,
        default=ClassificationReviewStatus.PENDING,
        server_default=ClassificationReviewStatus.PENDING.value,
    )
    assigned_technician_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[TicketStatus] = mapped_column(
        _enum_column(TicketStatus, "ticket_status"),
        nullable=False,
        default=TicketStatus.NEW,
        server_default=TicketStatus.NEW.value,
    )
    technician_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggested_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_solution_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", server_default="pending"
    )
    ai_solution_error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ai_solution_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class TicketSolutionSource(Base):
    """Passaggio recuperato e realmente citato in un suggerimento AI."""

    __tablename__ = "ticket_solution_sources"
    __table_args__ = (
        CheckConstraint("rank >= 1", name="ck_ticket_solution_sources_rank"),
        CheckConstraint(
            "similarity_score BETWEEN -1.0 AND 1.0",
            name="ck_ticket_solution_sources_score",
        ),
        UniqueConstraint("ticket_id", "rank", name="ux_ticket_solution_sources_ticket_rank"),
        UniqueConstraint(
            "ticket_id",
            "segment_id",
            name="ux_ticket_solution_sources_ticket_segment",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    segment_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_segments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class ProposedAction(Base):
    """Azione suggerita e salvata senza produrre alcun effetto operativo."""

    __tablename__ = "proposed_actions"
    __table_args__ = (
        CheckConstraint(
            "length(trim(rationale)) BETWEEN 20 AND 1000",
            name="ck_proposed_actions_rationale_length",
        ),
        CheckConstraint(
            "length(trim(expected_effect)) BETWEEN 10 AND 1000",
            name="ck_proposed_actions_expected_effect_length",
        ),
        CheckConstraint(
            "length(trim(payload_json)) >= 2",
            name="ck_proposed_actions_payload_present",
        ),
        Index("ix_proposed_actions_ticket_status", "ticket_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[ActionType] = mapped_column(
        _enum_column(ActionType, "action_type"), nullable=False
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    expected_effect: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        _enum_column(ActionStatus, "action_status"),
        nullable=False,
        default=ActionStatus.PENDING_APPROVAL,
        server_default=ActionStatus.PENDING_APPROVAL.value,
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    execution_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class AuditEvent(Base):
    """Evento append-only che documenta un passaggio rilevante del ticket."""

    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint(
            "length(trim(summary)) BETWEEN 5 AND 300",
            name="ck_audit_events_summary_length",
        ),
        CheckConstraint(
            "length(details_json) BETWEEN 2 AND 4000",
            name="ck_audit_events_details_length",
        ),
        Index("ix_audit_events_ticket_created", "ticket_id", "created_at", "id"),
        Index("ix_audit_events_type_created", "event_type", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    actor_type: Mapped[AuditActorType] = mapped_column(
        _enum_column(AuditActorType, "audit_actor_type"), nullable=False
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        _enum_column(AuditEventType, "audit_event_type"), nullable=False
    )
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    details_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}", server_default="{}"
    )
    action_id: Mapped[int | None] = mapped_column(
        ForeignKey("proposed_actions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_key: Mapped[str | None] = mapped_column(String(160), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


@sqlalchemy_event.listens_for(AuditEvent, "before_update")
@sqlalchemy_event.listens_for(AuditEvent, "before_delete")
def _prevent_audit_event_mutation(*_: object) -> None:
    """Impedisce modifiche o cancellazioni accidentali tramite l'ORM."""

    raise ValueError("Gli eventi di audit sono append-only")
