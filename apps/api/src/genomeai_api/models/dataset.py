from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.models.experiment import Experiment
    from genomeai_api.models.genome import Genome


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organism: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_public: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    genome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("genomes.id"),
        nullable=True,
        index=True,
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id"),
        nullable=True,
        index=True,
    )

    genome: Mapped[Genome | None] = relationship(
        "Genome", back_populates="datasets"
    )
    experiment: Mapped[Experiment | None] = relationship(
        "Experiment", back_populates="datasets"
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
