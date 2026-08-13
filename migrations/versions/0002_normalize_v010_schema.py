"""Normalizza la variante storica dello schema v0.1.0.

Revision ID: 0002_normalize_v010
Revises: 0001_v010_baseline
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_normalize_v010"
down_revision: str | None = "0001_v010_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CLASSIFICATION_REVIEW_CHECK = (
    "classification_review_status IN "
    "('pending', 'ai_suggested', 'human_reviewed', "
    "'ai_unavailable', 'ai_invalid_response')"
)
AI_SOLUTION_STATUS_CHECK = (
    "ai_solution_status IN ('pending', 'generated', 'unavailable', 'invalid_response')"
)


def _ticket_shape() -> tuple[int | None, set[str]]:
    inspector = sa.inspect(op.get_bind())
    classification_column = next(
        column
        for column in inspector.get_columns("tickets")
        if column["name"] == "classification_review_status"
    )
    check_names = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("tickets")
        if constraint["name"] is not None
    }
    return classification_column["type"].length, check_names


def upgrade() -> None:
    """Converge la variante creata dai vecchi ALTER verso lo schema canonico."""

    classification_length, check_names = _ticket_shape()
    missing_classification_check = "classification_review_status" not in check_names
    missing_solution_check = "ck_tickets_ai_solution_status" not in check_names
    if (
        classification_length == 19
        and not missing_classification_check
        and not missing_solution_check
    ):
        return

    with op.batch_alter_table("tickets", recreate="always") as batch_op:
        if classification_length != 19:
            batch_op.alter_column(
                "classification_review_status",
                existing_type=sa.String(length=classification_length),
                type_=sa.String(length=19),
                existing_nullable=False,
                existing_server_default="pending",
            )
        if missing_classification_check:
            batch_op.create_check_constraint(
                "classification_review_status",
                CLASSIFICATION_REVIEW_CHECK,
            )
        if missing_solution_check:
            batch_op.create_check_constraint(
                "ck_tickets_ai_solution_status",
                AI_SOLUTION_STATUS_CHECK,
            )


def downgrade() -> None:
    """La normalizzazione compatibile non altera lo schema baseline canonico."""
