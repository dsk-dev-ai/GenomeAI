from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.models.gene import Gene
    from genomeai_api.models.transcript import Transcript


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    variant_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    chromosome: Mapped[str] = mapped_column(String(10), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    ref: Mapped[str] = mapped_column(String(500), nullable=False)
    alt: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    filter_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    genome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("genomes.id"),
        nullable=True,
        index=True,
    )
    gene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("genes.id"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    gene: Mapped[Gene] = relationship(
        "Gene", back_populates="variants"
    )
    transcripts: Mapped[list[Transcript]] = relationship(
        "Transcript", back_populates="variant"
    )

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
