"""create projects table

Revision ID: 7cf6d6506732
Revises: df47a097676a
Create Date: 2026-07-23 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7cf6d6506732"
down_revision: str | None = "df47a097676a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.String(length=100), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("principal_investigator", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("genome_id", sa.UUID(), nullable=True),
        sa.Column("study_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["genome_id"], ["genomes.id"]),
        sa.ForeignKeyConstraint(["study_id"], ["studies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_projects_project_id"),
        "projects",
        ["project_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_projects_genome_id"),
        "projects",
        ["genome_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_projects_study_id"),
        "projects",
        ["study_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_study_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_genome_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_project_id"), table_name="projects")
    op.drop_table("projects")
