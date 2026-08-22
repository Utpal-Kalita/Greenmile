"""Add persisted Azure OpenAI analyses.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("optimization_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(60), nullable=False),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("predictions", postgresql.JSONB(), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False),
        sa.Column("latency_ms", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_analyses_optimization_run_id", "ai_analyses", ["optimization_run_id"])
    op.create_index("ix_ai_analyses_status", "ai_analyses", ["status"])


def downgrade() -> None:
    op.drop_table("ai_analyses")
