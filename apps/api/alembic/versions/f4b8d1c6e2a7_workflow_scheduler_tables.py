"""workflow scheduler tables

Revision ID: f4b8d1c6e2a7
Revises: e8b2c4d6f9a3
Create Date: 2026-08-24 00:00:00.000000

Phase 7.3 (Workflow Scheduler) adds workflow_schedules and annotates the
existing workflow_runs table so every scheduled run records which schedule
created it and for which occurrence. The partial unique index on
(schedule_id, scheduled_for) makes duplicate creation of the same
occurrence impossible at the database level.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f4b8d1c6e2a7"
down_revision: str | None = "e8b2c4d6f9a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workflow_schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workflow_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("schedule_type", sa.String(length=50), nullable=False),
        sa.Column("expression", sa.String(length=255), nullable=True),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "timezone_name",
            sa.String(length=64),
            nullable=False,
            server_default="UTC",
        ),
        sa.Column(
            "state",
            sa.String(length=50),
            nullable=False,
            server_default="enabled",
        ),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "schedule_type IN ('once', 'recurring')",
            name="ck_schedule_type",
        ),
        sa.CheckConstraint(
            "state IN ('enabled', 'disabled', 'completed')",
            name="ck_schedule_state",
        ),
        sa.CheckConstraint(
            "("
            "(schedule_type = 'once' AND run_at IS NOT NULL AND expression IS NULL)"
            " OR "
            "(schedule_type = 'recurring' AND expression IS NOT NULL AND run_at IS NULL)"
            ")",
            name="ck_schedule_shape_matches_type",
        ),
    )
    op.create_index(
        "ix_workflow_schedules_workflow_id",
        "workflow_schedules",
        ["workflow_id"],
    )
    op.create_index(
        "ix_workflow_schedules_state_next_run",
        "workflow_schedules",
        ["state", "next_run_at"],
    )

    op.add_column(
        "workflow_runs",
        sa.Column(
            "schedule_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workflow_schedules.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workflow_runs_schedule_id", "workflow_runs", ["schedule_id"])
    op.create_index(
        "uq_workflow_runs_schedule_occurrence",
        "workflow_runs",
        ["schedule_id", "scheduled_for"],
        unique=True,
        postgresql_where=sa.text(
            "schedule_id IS NOT NULL AND scheduled_for IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_workflow_runs_schedule_occurrence",
        table_name="workflow_runs",
    )
    op.drop_index("ix_workflow_runs_schedule_id", table_name="workflow_runs")
    op.drop_column("workflow_runs", "scheduled_for")
    op.drop_column("workflow_runs", "schedule_id")
    op.drop_index(
        "ix_workflow_schedules_state_next_run",
        table_name="workflow_schedules",
    )
    op.drop_index(
        "ix_workflow_schedules_workflow_id",
        table_name="workflow_schedules",
    )
    op.drop_table("workflow_schedules")
