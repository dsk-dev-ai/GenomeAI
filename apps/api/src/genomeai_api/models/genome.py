from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.models.dataset import Dataset
    from genomeai_api.models.experiment import Experiment
    from genomeai_api.models.protein import Protein
    from genomeai_api.models.transcript import Transcript


class Genome(Base):
    __tablename__ = "genomes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    accession: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    organism: Mapped[str] = mapped_column(String(255), nullable=False)
    assembly: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    datasets: Mapped[list[Dataset]] = relationship(
        "Dataset", back_populates="genome"
    )
    experiments: Mapped[list[Experiment]] = relationship(
        "Experiment", back_populates="genome"
    )
    transcripts: Mapped[list[Transcript]] = relationship(
        "Transcript", back_populates="genome"
    )
    proteins: Mapped[list[Protein]] = relationship(
        "Protein", back_populates="genome"
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
