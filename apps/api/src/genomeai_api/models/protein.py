from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.models.gene import Gene
    from genomeai_api.models.genome import Genome
    from genomeai_api.models.transcript import Transcript


class Protein(Base):
    __tablename__ = "proteins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    protein_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    protein_name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    accession: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    sequence: Mapped[str | None] = mapped_column(Text, nullable=True)
    length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    molecular_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    organism: Mapped[str | None] = mapped_column(String(255), nullable=True)
    function: Mapped[str | None] = mapped_column(Text, nullable=True)
    gene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("genes.id"),
        nullable=True,
        index=True,
    )
    transcript_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcripts.id"),
        nullable=True,
        index=True,
    )
    genome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("genomes.id"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    gene: Mapped[Gene | None] = relationship(
        "Gene", back_populates="proteins"
    )
    transcript: Mapped[Transcript | None] = relationship(
        "Transcript", back_populates="proteins"
    )
    genome: Mapped[Genome | None] = relationship(
        "Genome", back_populates="proteins"
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
