"""Aggiunge metadati privati per gli allegati controllati.

Revision ID: 0004_secure_attachments
Revises: 0003_support_groups
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_secure_attachments"
down_revision: str | None = "0003_support_groups"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea il catalogo privato e polimorfico degli allegati."""

    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "context_type",
            sa.Enum(
                "draft",
                "ticket",
                "message",
                name="attachment_context_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("context_id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_filename", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint("context_id > 0", name="ck_attachments_context_id"),
        sa.CheckConstraint("size_bytes > 0", name="ck_attachments_size"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_filename"),
    )
    op.create_index("ix_attachments_checksum_sha256", "attachments", ["checksum_sha256"])
    op.create_index("ix_attachments_context", "attachments", ["context_type", "context_id"])
    op.create_index("ix_attachments_owner_user_id", "attachments", ["owner_user_id"])


def downgrade() -> None:
    """Rimuove soltanto il catalogo aggiunto da questa revisione."""

    op.drop_index("ix_attachments_owner_user_id", table_name="attachments")
    op.drop_index("ix_attachments_context", table_name="attachments")
    op.drop_index("ix_attachments_checksum_sha256", table_name="attachments")
    op.drop_table("attachments")
