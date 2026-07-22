from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TranscriptBase(BaseModel):
    transcript_id: str = Field(max_length=50)
    transcript_name: str = Field(max_length=255)
    transcript_type: str | None = Field(default=None, max_length=50)
    chromosome: str = Field(max_length=10)
    strand: str | None = Field(default=None, max_length=1)
    start_position: int | None = None
    end_position: int | None = None
    length: int | None = None
    genome_id: uuid.UUID | None = None
    gene_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str | None = None


class TranscriptCreate(TranscriptBase):
    pass


class TranscriptUpdate(BaseModel):
    transcript_id: str | None = Field(default=None, max_length=50)
    transcript_name: str | None = Field(default=None, max_length=255)
    transcript_type: str | None = Field(default=None, max_length=50)
    chromosome: str | None = Field(default=None, max_length=10)
    strand: str | None = Field(default=None, max_length=1)
    start_position: int | None = None
    end_position: int | None = None
    length: int | None = None
    genome_id: uuid.UUID | None = None
    gene_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str | None = None


class TranscriptResponse(TranscriptBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
