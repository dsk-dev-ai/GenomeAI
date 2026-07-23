"""create datasets table

Revision ID: f90b9cf85ea9
Revises: 2325f8c4566c
Create Date: 2026-07-23 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f90b9cf85ea9"
down_revision: str | None = "2325f8c4566c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("dataset_id", sa.String(length=100), nullable=False),
        sa.Column("dataset_name", sa.String(length=255), nullable=False),
        sa.Column("dataset_type", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("organism", sa.String(length=255), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("genome_id", sa.UUID(), nullable=True),
        sa.Column("experiment_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_datasets_dataset_id"),
        "datasets",
        ["dataset_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_datasets_genome_id"),
        "datasets",
        ["genome_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_datasets_experiment_id"),
        "datasets",
        ["experiment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_datasets_experiment_id"), table_name="datasets")
    op.drop_index(op.f("ix_datasets_genome_id"), table_name="datasets")
    op.drop_index(op.f("ix_datasets_dataset_id"), table_name="datasets")
    op.drop_table("datasets")
