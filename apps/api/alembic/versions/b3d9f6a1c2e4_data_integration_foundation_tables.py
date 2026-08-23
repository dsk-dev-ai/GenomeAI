"""data integration foundation tables

Revision ID: b3d9f6a1c2e4
Revises: 7cf6d6506732
Create Date: 2026-08-23 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "b3d9f6a1c2e4"
down_revision: str | None = "7cf6d6506732"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column(
            "source_type", sa.String(length=50), nullable=False, server_default="other"
        ),
        sa.Column("api_base_url", sa.String(length=500), nullable=False),
        sa.Column("documentation_url", sa.String(length=500), nullable=True),
        sa.Column("auth_mode", sa.String(length=50), nullable=False, server_default="none"),
        sa.Column("credential_ref", sa.String(length=255), nullable=True),
        sa.Column("rate_limit", JSONB(), nullable=False, server_default="{}"),
        sa.Column("license_info", JSONB(), nullable=False, server_default="{}"),
        sa.Column("access_mode", sa.String(length=50), nullable=False, server_default="live"),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "sync_status", sa.String(length=50), nullable=False, server_default="unknown"
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("feature_flags", JSONB(), nullable=False, server_default="{}"),
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
    )
    op.create_index(
        op.f("ix_data_sources_source_id"), "data_sources", ["source_id"], unique=True
    )

    op.create_table(
        "provenance",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.source_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provenance_source_record",
        "provenance",
        ["source_id", "source_record_id"],
        unique=False,
    )

    op.create_table(
        "external_identifiers",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("genomeai_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=100), nullable=True),
        sa.Column("version", sa.String(length=100), nullable=True),
        sa.Column("provenance_id", UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.source_id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_external_identifiers_source_id"),
        "external_identifiers",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_external_identifiers_entity",
        "external_identifiers",
        ["entity_type", "genomeai_entity_id"],
        unique=False,
    )
    op.create_index(
        "uq_external_identifier",
        "external_identifiers",
        ["source_id", "external_id", "entity_type"],
        unique=True,
        postgresql_where=sa.text("namespace IS NULL"),
    )
    op.create_index(
        "uq_external_identifier_ns",
        "external_identifiers",
        ["source_id", "external_id", "entity_type", "namespace"],
        unique=True,
        postgresql_where=sa.text("namespace IS NOT NULL"),
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "records_received", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "records_succeeded", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "records_failed", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_detail", JSONB(), nullable=True),
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
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.source_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ingestion_jobs_source_id"), "ingestion_jobs", ["source_id"], unique=False
    )
    op.create_index(
        "ix_ingestion_jobs_source_state",
        "ingestion_jobs",
        ["source_id", "state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_jobs_source_state", table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_source_id"), table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")

    op.drop_index("uq_external_identifier_ns", table_name="external_identifiers")
    op.drop_index("uq_external_identifier", table_name="external_identifiers")
    op.drop_index(
        "ix_external_identifiers_entity", table_name="external_identifiers"
    )
    op.drop_index(
        op.f("ix_external_identifiers_source_id"), table_name="external_identifiers"
    )
    op.drop_table("external_identifiers")

    op.drop_index("ix_provenance_source_record", table_name="provenance")
    op.drop_table("provenance")

    op.drop_index(op.f("ix_data_sources_source_id"), table_name="data_sources")
    op.drop_table("data_sources")
