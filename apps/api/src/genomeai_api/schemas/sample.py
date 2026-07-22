from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SampleBase(BaseModel):
    sample_id: str = Field(max_length=100)
    sample_name: str = Field(max_length=255)
    organism: str = Field(max_length=255)
    tissue: str | None = Field(default=None, max_length=255)
    cell_type: str | None = Field(default=None, max_length=255)
    disease: str | None = Field(default=None, max_length=255)
    phenotype: str | None = Field(default=None, max_length=255)
    sex: str | None = Field(default=None, max_length=20)
    age: str | None = Field(default=None, max_length=50)
    genome_id: uuid.UUID | None = None
    description: str | None = None


class SampleCreate(SampleBase):
    pass


class SampleUpdate(BaseModel):
    sample_id: str | None = Field(default=None, max_length=100)
    sample_name: str | None = Field(default=None, max_length=255)
    organism: str | None = Field(default=None, max_length=255)
    tissue: str | None = Field(default=None, max_length=255)
    cell_type: str | None = Field(default=None, max_length=255)
    disease: str | None = Field(default=None, max_length=255)
    phenotype: str | None = Field(default=None, max_length=255)
    sex: str | None = Field(default=None, max_length=20)
    age: str | None = Field(default=None, max_length=50)
    genome_id: uuid.UUID | None = None
    description: str | None = None


class SampleResponse(SampleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
