from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.models.experiment import Experiment


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    sample_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    sample_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organism: Mapped[str] = mapped_column(String(255), nullable=False)
    tissue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cell_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    disease: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phenotype: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age: Mapped[str | None] = mapped_column(String(50), nullable=True)
    genome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("genomes.id"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    experiments: Mapped[list[Experiment]] = relationship(
        "Experiment", back_populates="sample"
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
