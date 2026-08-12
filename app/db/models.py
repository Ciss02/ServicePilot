"""Tabelle iniziali persistenti di ServicePilot."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.vocabulary import (
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
    """Documento amministrativo conservato prima della futura indicizzazione."""

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_knowledge_documents_size"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_filename: Mapped[str] = mapped_column(
        String(80), nullable=False, unique=True
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
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
    impact: Mapped[Impact | None] = mapped_column(
        _enum_column(Impact, "impact"), nullable=True
    )
    urgency: Mapped[Urgency | None] = mapped_column(
        _enum_column(Urgency, "urgency"), nullable=True
    )
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

