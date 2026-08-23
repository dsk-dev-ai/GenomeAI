from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from genomeai_api.database.base import Base


class Provenance(Base):
    """Traceability for imported external records.

    ``source_version`` stays NULL until a connector reports a real release;
    GenomeAI never fabricates one.
    """

    __tablename__ = "provenance"
    __table_args__ = (
        Index("ix_provenance_source_record", "source_id", "source_record_id"),
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
    )
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
