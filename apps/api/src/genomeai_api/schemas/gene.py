from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GeneBase(BaseModel):
    gene_id: str = Field(max_length=50)
    gene_name: str = Field(max_length=255)
    chromosome: str = Field(max_length=10)
    strand: str | None = Field(default=None, max_length=1)
    start_position: int | None = None
    end_position: int | None = None
    biotype: str | None = Field(default=None, max_length=50)
    description: str | None = None
    genome_id: uuid.UUID | None = None


class GeneCreate(GeneBase):
    pass


class GeneUpdate(BaseModel):
    gene_id: str | None = Field(default=None, max_length=50)
    gene_name: str | None = Field(default=None, max_length=255)
    chromosome: str | None = Field(default=None, max_length=10)
    strand: str | None = Field(default=None, max_length=1)
    start_position: int | None = None
    end_position: int | None = None
    biotype: str | None = Field(default=None, max_length=50)
    description: str | None = None
    genome_id: uuid.UUID | None = None


class GeneResponse(GeneBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
