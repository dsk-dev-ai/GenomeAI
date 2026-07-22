from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProteinBase(BaseModel):
    protein_id: str = Field(max_length=50)
    protein_name: str = Field(max_length=255)
    symbol: str | None = Field(default=None, max_length=50)
    accession: str | None = Field(default=None, max_length=50)
    sequence: str | None = None
    length: int | None = Field(default=None, ge=0)
    molecular_weight: float | None = Field(default=None, ge=0)
    organism: str | None = Field(default=None, max_length=255)
    function: str | None = None
    gene_id: uuid.UUID | None = None
    transcript_id: uuid.UUID | None = None
    genome_id: uuid.UUID | None = None
    description: str | None = None


class ProteinCreate(ProteinBase):
    pass


class ProteinUpdate(BaseModel):
    protein_id: str | None = Field(default=None, max_length=50)
    protein_name: str | None = Field(default=None, max_length=255)
    symbol: str | None = Field(default=None, max_length=50)
    accession: str | None = Field(default=None, max_length=50)
    sequence: str | None = None
    length: int | None = Field(default=None, ge=0)
    molecular_weight: float | None = Field(default=None, ge=0)
    organism: str | None = Field(default=None, max_length=255)
    function: str | None = None
    gene_id: uuid.UUID | None = None
    transcript_id: uuid.UUID | None = None
    genome_id: uuid.UUID | None = None
    description: str | None = None


class ProteinResponse(ProteinBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
