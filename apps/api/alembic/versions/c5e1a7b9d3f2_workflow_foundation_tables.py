"""workflow foundation tables

Revision ID: c5e1a7b9d3f2
Revises: b3d9f6a1c2e4
Create Date: 2026-08-23 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "c5e1a7b9d3f2"
down_revision: str | None = "b3d9f6a1c2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workflows",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="0.1.0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'archived')", name="ck_workflow_status"
        ),
    )
    op.create_index(op.f("ix_workflows_name"), "workflows", ["name"], unique=False)

    op.create_table(
        "workflow_steps",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("step_type", sa.String(length=100), nullable=False),
        sa.Column("configuration", JSONB(), nullable=False, server_default="{}"),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"], ["workflows.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "name", name="uq_workflow_step_name"),
        sa.UniqueConstraint("workflow_id", "id", name="uq_workflow_step_scope"),
    )
    op.create_index(
        op.f("ix_workflow_steps_workflow_id"), "workflow_steps", ["workflow_id"]
    )
    op.create_index(
        "ix_workflow_steps_workflow_position",
        "workflow_steps",
        ["workflow_id", "position"],
    )

    op.create_table(
        "workflow_dependencies",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", UUID(as_uuid=True), nullable=False),
        sa.Column("from_step_id", UUID(as_uuid=True), nullable=False),
        sa.Column("to_step_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"], ["workflows.id"], ondelete="CASCADE"
        ),
        # Composite FKs scope BOTH endpoints to this row's own workflow, so a
        # dependency can never connect steps from different workflows.
        sa.ForeignKeyConstraint(
            ["workflow_id", "from_step_id"],
            ["workflow_steps.workflow_id", "workflow_steps.id"],
            name="fk_workflow_dependency_from_step",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id", "to_step_id"],
            ["workflow_steps.workflow_id", "workflow_steps.id"],
            name="fk_workflow_dependency_to_step",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "from_step_id <> to_step_id", name="ck_workflow_dependency_not_self"
        ),
        sa.UniqueConstraint("from_step_id", "to_step_id", name="uq_workflow_dependency_edge"),
    )
    op.create_index(
        op.f("ix_workflow_dependencies_workflow_id"),
        "workflow_dependencies",
        ["workflow_id"],
    )
    op.create_index(
        op.f("ix_workflow_dependencies_from_step_id"),
        "workflow_dependencies",
        ["from_step_id"],
    )
    op.create_index(
        op.f("ix_workflow_dependencies_to_step_id"),
        "workflow_dependencies",
        ["to_step_id"],
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"], ["workflows.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_runs_workflow_id"), "workflow_runs", ["workflow_id"])
    op.create_index(
        "ix_workflow_runs_workflow_state", "workflow_runs", ["workflow_id", "state"]
    )

    op.create_table(
        "workflow_step_runs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["step_id"], ["workflow_steps.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "step_id", name="uq_workflow_step_run"),
    )
    op.create_index(op.f("ix_workflow_step_runs_run_id"), "workflow_step_runs", ["run_id"])
    op.create_index(
        op.f("ix_workflow_step_runs_step_id"), "workflow_step_runs", ["step_id"]
    )
    op.create_index(
        "ix_workflow_step_runs_run_state", "workflow_step_runs", ["run_id", "state"]
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_step_runs_run_state", table_name="workflow_step_runs")
    op.drop_index(op.f("ix_workflow_step_runs_step_id"), table_name="workflow_step_runs")
    op.drop_index(op.f("ix_workflow_step_runs_run_id"), table_name="workflow_step_runs")
    op.drop_table("workflow_step_runs")

    op.drop_index("ix_workflow_runs_workflow_state", table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_workflow_id"), table_name="workflow_runs")
    op.drop_table("workflow_runs")

    op.drop_index(
        op.f("ix_workflow_dependencies_to_step_id"), table_name="workflow_dependencies"
    )
    op.drop_index(
        op.f("ix_workflow_dependencies_from_step_id"), table_name="workflow_dependencies"
    )
    op.drop_index(
        op.f("ix_workflow_dependencies_workflow_id"), table_name="workflow_dependencies"
    )
    op.drop_table("workflow_dependencies")

    op.drop_index(
        "ix_workflow_steps_workflow_position", table_name="workflow_steps"
    )
    op.drop_index(op.f("ix_workflow_steps_workflow_id"), table_name="workflow_steps")
    op.drop_table("workflow_steps")

    op.drop_index(op.f("ix_workflows_name"), table_name="workflows")
    op.drop_table("workflows")
