"""Add Azure OpenAI lifecycle event types.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-22
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'AI_ANALYSIS_STARTED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'AI_ANALYSIS_COMPLETE'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'AI_ANALYSIS_FAILED'")


def downgrade() -> None:
    # PostgreSQL enum values are intentionally retained; removing them requires recreating the type.
    pass
