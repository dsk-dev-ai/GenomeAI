from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GenomeBase(BaseModel):
    accession: str = Field(max_length=50)
    organism: str = Field(max_length=255)
    assembly: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=100)
    description: str | None = None


class GenomeCreate(GenomeBase):
    pass


class GenomeUpdate(BaseModel):
    accession: str | None = Field(default=None, max_length=50)
    organism: str | None = Field(default=None, max_length=255)
    assembly: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=100)
    description: str | None = None


class GenomeResponse(GenomeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
