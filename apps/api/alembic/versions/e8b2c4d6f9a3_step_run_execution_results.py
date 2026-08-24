"""step run execution results

Revision ID: e8b2c4d6f9a3
Revises: c5e1a7b9d3f2
Create Date: 2026-08-24 00:00:00.000000

Phase 7.2 (DAG execution engine) needs to persist per-step results:
successful outputs and preserved failure reasons. Phase 7.1 had no
columns for either, so this extends workflow_step_runs only.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "e8b2c4d6f9a3"
down_revision: str | None = "c5e1a7b9d3f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_step_runs",
        sa.Column("output", JSONB(), nullable=True),
    )
    op.add_column(
        "workflow_step_runs",
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_step_runs", "error_message")
    op.drop_column("workflow_step_runs", "output")
