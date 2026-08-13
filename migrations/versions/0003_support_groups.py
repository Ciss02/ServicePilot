"""Aggiunge il catalogo amministrabile dei gruppi di supporto.

Revision ID: 0003_support_groups
Revises: 0002_normalize_v010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_support_groups"
down_revision: str | None = "0002_normalize_v010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea catalogo e appartenenze senza alterare lo storico dei ticket."""

    op.create_table(
        "support_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_key", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
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
            "length(trim(description)) BETWEEN 2 AND 500",
            name="ck_support_groups_description_length",
        ),
        sa.CheckConstraint(
            "length(trim(name)) BETWEEN 2 AND 100",
            name="ck_support_groups_name_length",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_key"),
    )
    op.create_table(
        "support_group_memberships",
        sa.Column("support_group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["support_group_id"], ["support_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("support_group_id", "user_id"),
    )


def downgrade() -> None:
    """Rimuove soltanto il catalogo, lasciando intatti i testi storici dei ticket."""

    op.drop_table("support_group_memberships")
    op.drop_table("support_groups")
