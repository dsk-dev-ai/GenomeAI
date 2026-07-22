from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from genomeai_api.database.base import Base


class Gene(Base):
    __tablename__ = "genes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    gene_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    gene_name: Mapped[str] = mapped_column(String(255), nullable=False)
    chromosome: Mapped[str] = mapped_column(String(10), nullable=False)
    strand: Mapped[str | None] = mapped_column(String(1), nullable=True)
    start_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    biotype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    genome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("genomes.id"),
        nullable=True,
        index=True,
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
