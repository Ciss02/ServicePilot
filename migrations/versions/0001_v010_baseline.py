"""Baseline dello schema pubblicato con ServicePilot v0.1.0.

Revision ID: 0001_v010_baseline
Revises: nessuna
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_v010_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea lo schema completo e immutabile della release v0.1.0."""

    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "employee",
                "technician",
                "admin",
                name="role",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_filename", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "extraction_status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("extraction_error", sa.String(length=300), nullable=True),
        sa.Column(
            "index_status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("index_error", sa.String(length=300), nullable=True),
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "embedding_dimensions IS NULL OR embedding_dimensions > 0",
            name="ck_knowledge_documents_embedding_dimensions",
        ),
        sa.CheckConstraint(
            "extraction_status IN ('pending', 'ready', 'failed')",
            name="ck_knowledge_documents_extraction_status",
        ),
        sa.CheckConstraint(
            "index_status IN ('pending', 'ready', 'failed')",
            name="ck_knowledge_documents_index_status",
        ),
        sa.CheckConstraint("size_bytes > 0", name="ck_knowledge_documents_size"),
        sa.ForeignKeyConstraint(
            ["uploaded_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_filename"),
    )
    op.create_index(
        "ix_knowledge_documents_checksum_sha256",
        "knowledge_documents",
        ["checksum_sha256"],
    )
    op.create_index(
        "ix_knowledge_documents_uploaded_by_user_id",
        "knowledge_documents",
        ["uploaded_by_user_id"],
    )
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("service", sa.String(length=100), nullable=False),
        sa.Column("affected_users", sa.Integer(), nullable=False),
        sa.Column("creation_key", sa.String(length=64), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "account_and_access",
                "devices_and_hardware",
                "software_and_applications",
                "network_and_connectivity",
                "printers_and_labeling",
                "telephony",
                "retail_systems",
                "production_systems",
                "information_security",
                "other_requests",
                name="ticket_category",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column(
            "impact",
            sa.Enum(
                "low",
                "medium",
                "high",
                name="impact",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column(
            "urgency",
            sa.Enum(
                "low",
                "medium",
                "high",
                name="urgency",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column(
            "priority",
            sa.Enum(
                "p1",
                "p2",
                "p3",
                "p4",
                name="priority",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column("assigned_group", sa.String(length=100), nullable=True),
        sa.Column(
            "classification_review_status",
            sa.Enum(
                "pending",
                "ai_suggested",
                "human_reviewed",
                "ai_unavailable",
                "ai_invalid_response",
                name="classification_review_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("assigned_technician_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "new",
                "in_progress",
                "waiting_for_requester",
                "waiting_for_vendor",
                "resolved",
                "closed",
                name="ticket_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="new",
            nullable=False,
        ),
        sa.Column("technician_note", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("ai_suggested_solution", sa.Text(), nullable=True),
        sa.Column(
            "ai_solution_status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("ai_solution_error", sa.String(length=300), nullable=True),
        sa.Column("ai_solution_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "affected_users BETWEEN 1 AND 10000",
            name="ck_tickets_affected_users",
        ),
        sa.CheckConstraint(
            "ai_solution_status IN ('pending', 'generated', 'unavailable', 'invalid_response')",
            name="ck_tickets_ai_solution_status",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_technician_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tickets_assigned_technician_id",
        "tickets",
        ["assigned_technician_id"],
    )
    op.create_index("ix_tickets_requester_id", "tickets", ["requester_id"])
    op.create_index("ix_tickets_site_id", "tickets", ["site_id"])
    op.create_index("ux_tickets_creation_key", "tickets", ["creation_key"], unique=True)
    op.create_table(
        "knowledge_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source_section", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("embedding_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "character_count > 0",
            name="ck_knowledge_segments_character_count",
        ),
        sa.CheckConstraint("position >= 0", name="ck_knowledge_segments_position"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "position",
            name="ux_knowledge_segments_document_position",
        ),
    )
    op.create_index(
        "ix_knowledge_segments_document_id",
        "knowledge_segments",
        ["document_id"],
    )
    op.create_table(
        "proposed_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column(
            "action_type",
            sa.Enum(
                "assign_ticket",
                "notify_requester",
                "escalate_vendor",
                name="action_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("expected_effect", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_approval",
                "approved",
                "rejected",
                "executing",
                "succeeded",
                "failed",
                name="action_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="pending_approval",
            nullable=False,
        ),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_reference", sa.String(length=80), nullable=True),
        sa.Column("execution_message", sa.Text(), nullable=True),
        sa.Column("execution_error_code", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(expected_effect)) BETWEEN 10 AND 1000",
            name="ck_proposed_actions_expected_effect_length",
        ),
        sa.CheckConstraint(
            "length(trim(payload_json)) >= 2",
            name="ck_proposed_actions_payload_present",
        ),
        sa.CheckConstraint(
            "length(trim(rationale)) BETWEEN 20 AND 1000",
            name="ck_proposed_actions_rationale_length",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_proposed_actions_reviewed_by_user_id",
        "proposed_actions",
        ["reviewed_by_user_id"],
    )
    op.create_index("ix_proposed_actions_ticket_id", "proposed_actions", ["ticket_id"])
    op.create_index(
        "ix_proposed_actions_ticket_status",
        "proposed_actions",
        ["ticket_id", "status"],
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column(
            "actor_type",
            sa.Enum(
                "human",
                "ai",
                "system",
                name="audit_actor_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "ticket_created",
                "ticket_updated",
                "ticket_status_changed",
                "ticket_assignment_changed",
                "ai_classification_suggested",
                "ai_classification_unavailable",
                "ai_classification_invalid",
                "classification_reviewed",
                "ai_solution_generated",
                "ai_solution_unavailable",
                "ai_solution_invalid",
                "action_proposed",
                "action_approved",
                "action_rejected",
                "action_execution_started",
                "action_execution_succeeded",
                "action_execution_failed",
                name="audit_event_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("summary", sa.String(length=300), nullable=False),
        sa.Column("details_json", sa.Text(), server_default="{}", nullable=False),
        sa.Column("action_id", sa.Integer(), nullable=True),
        sa.Column("event_key", sa.String(length=160), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(details_json) BETWEEN 2 AND 4000",
            name="ck_audit_events_details_length",
        ),
        sa.CheckConstraint(
            "length(trim(summary)) BETWEEN 5 AND 300",
            name="ck_audit_events_summary_length",
        ),
        sa.ForeignKeyConstraint(["action_id"], ["proposed_actions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key"),
    )
    op.create_index("ix_audit_events_action_id", "audit_events", ["action_id"])
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index(
        "ix_audit_events_ticket_created",
        "audit_events",
        ["ticket_id", "created_at", "id"],
    )
    op.create_index("ix_audit_events_ticket_id", "audit_events", ["ticket_id"])
    op.create_index(
        "ix_audit_events_type_created",
        "audit_events",
        ["event_type", "created_at"],
    )
    op.create_table(
        "ticket_solution_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint("rank >= 1", name="ck_ticket_solution_sources_rank"),
        sa.CheckConstraint(
            "similarity_score BETWEEN -1.0 AND 1.0",
            name="ck_ticket_solution_sources_score",
        ),
        sa.ForeignKeyConstraint(
            ["segment_id"],
            ["knowledge_segments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ticket_id",
            "rank",
            name="ux_ticket_solution_sources_ticket_rank",
        ),
        sa.UniqueConstraint(
            "ticket_id",
            "segment_id",
            name="ux_ticket_solution_sources_ticket_segment",
        ),
    )
    op.create_index(
        "ix_ticket_solution_sources_segment_id",
        "ticket_solution_sources",
        ["segment_id"],
    )
    op.create_index(
        "ix_ticket_solution_sources_ticket_id",
        "ticket_solution_sources",
        ["ticket_id"],
    )


def downgrade() -> None:
    """Rimuove lo schema baseline soltanto su richiesta esplicita."""

    op.drop_table("ticket_solution_sources")
    op.drop_table("audit_events")
    op.drop_table("proposed_actions")
    op.drop_table("knowledge_segments")
    op.drop_table("tickets")
    op.drop_table("knowledge_documents")
    op.drop_table("auth_sessions")
    op.drop_table("users")
    op.drop_table("sites")
