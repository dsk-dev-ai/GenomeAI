"""create studies table

Revision ID: df47a097676a
Revises: f90b9cf85ea9
Create Date: 2026-07-23 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "df47a097676a"
down_revision: str | None = "f90b9cf85ea9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "studies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("study_id", sa.String(length=100), nullable=False),
        sa.Column("study_name", sa.String(length=255), nullable=False),
        sa.Column("study_type", sa.String(length=100), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organism", sa.String(length=255), nullable=True),
        sa.Column("institution", sa.String(length=255), nullable=True),
        sa.Column("principal_investigator", sa.String(length=255), nullable=True),
        sa.Column("publication", sa.String(length=500), nullable=True),
        sa.Column("doi", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("genome_id", sa.UUID(), nullable=True),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_studies_study_id"),
        "studies",
        ["study_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_studies_genome_id"),
        "studies",
        ["genome_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_studies_dataset_id"),
        "studies",
        ["dataset_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_studies_dataset_id"), table_name="studies")
    op.drop_index(op.f("ix_studies_genome_id"), table_name="studies")
    op.drop_index(op.f("ix_studies_study_id"), table_name="studies")
    op.drop_table("studies")
