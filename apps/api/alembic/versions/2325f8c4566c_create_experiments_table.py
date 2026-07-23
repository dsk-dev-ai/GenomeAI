"""create experiments table

Revision ID: 2325f8c4566c
Revises: cc42f7960492
Create Date: 2026-07-23 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2325f8c4566c"
down_revision: str | None = "cc42f7960492"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("experiment_id", sa.String(length=100), nullable=False),
        sa.Column("experiment_name", sa.String(length=255), nullable=False),
        sa.Column("experiment_type", sa.String(length=100), nullable=True),
        sa.Column("platform", sa.String(length=100), nullable=True),
        sa.Column("technology", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("organism", sa.String(length=255), nullable=True),
        sa.Column("laboratory", sa.String(length=255), nullable=True),
        sa.Column("researcher", sa.String(length=255), nullable=True),
        sa.Column("sample_id", sa.UUID(), nullable=True),
        sa.Column("genome_id", sa.UUID(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["sample_id"], ["samples.id"]),
        sa.ForeignKeyConstraint(["genome_id"], ["genomes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_experiments_experiment_id"),
        "experiments",
        ["experiment_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_experiments_sample_id"),
        "experiments",
        ["sample_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_experiments_genome_id"),
        "experiments",
        ["genome_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_experiments_genome_id"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_sample_id"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_experiment_id"), table_name="experiments")
    op.drop_table("experiments")
