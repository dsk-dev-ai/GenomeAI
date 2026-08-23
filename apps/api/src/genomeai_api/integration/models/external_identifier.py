from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base
from genomeai_api.integration.models.provenance import Provenance


class ExternalIdentifier(Base):
    """Maps one external record id to a GenomeAI internal entity.

    Uniqueness of (source_id, external_id, entity_type) is enforced with two
    partial unique indexes so the optional namespace never collides with NULL.
    """

    __tablename__ = "external_identifiers"
    __table_args__ = (
        Index(
            "uq_external_identifier",
            "source_id",
            "external_id",
            "entity_type",
            unique=True,
            postgresql_where=text("namespace IS NULL"),
        ),
        Index(
            "uq_external_identifier_ns",
            "source_id",
            "external_id",
            "entity_type",
            "namespace",
            unique=True,
            postgresql_where=text("namespace IS NOT NULL"),
        ),
        Index(
            "ix_external_identifiers_entity",
            "entity_type",
            "genomeai_entity_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("data_sources.source_id"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    genomeai_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    namespace: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provenance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provenance.id"),
        nullable=True,
    )
    provenance: Mapped[Provenance | None] = relationship("Provenance")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
