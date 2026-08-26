"""workflow run retry tracking

Revision ID: a7c3d9e1b5f8
Revises: f4b8d1c6e2a7
Create Date: 2026-08-25 00:00:00.000000

Phase 7.5 (Workflow Retry & Failure Handling) extends workflow_runs with
attempt and failure metadata:

- attempt_count: how many EXECUTION attempts have started (incremented
  when the engine moves a run to running); the retry budget is compared
  against this persisted number, so duplicate queue messages or worker
  crashes can never exceed max_attempts.
- failure_class: deterministic classification of the most recent failure.
- next_retry_at: when an automatic retry is scheduled (NULL otherwise).
- failure_history: append-only JSONB list of per-attempt failure entries
  {attempt, class, reason, failed_at}; previous attempts are never
  silently overwritten.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a7c3d9e1b5f8"
down_revision: str | None = "f4b8d1c6e2a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("failure_class", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("failure_history", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_runs", "failure_history")
    op.drop_column("workflow_runs", "next_retry_at")
    op.drop_column("workflow_runs", "failure_class")
    op.drop_column("workflow_runs", "attempt_count")
