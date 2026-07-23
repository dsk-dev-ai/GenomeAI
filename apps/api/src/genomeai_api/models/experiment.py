from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.models.dataset import Dataset
    from genomeai_api.models.genome import Genome
    from genomeai_api.models.sample import Sample


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    experiment_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    experiment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    experiment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    technology: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    organism: Mapped[str | None] = mapped_column(String(255), nullable=True)
    laboratory: Mapped[str | None] = mapped_column(String(255), nullable=True)
    researcher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("samples.id"),
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

    datasets: Mapped[list[Dataset]] = relationship(
        "Dataset", back_populates="experiment"
    )
    sample: Mapped[Sample | None] = relationship(
        "Sample", back_populates="experiments"
    )
    genome: Mapped[Genome | None] = relationship(
        "Genome", back_populates="experiments"
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
