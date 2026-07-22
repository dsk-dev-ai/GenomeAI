from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VariantBase(BaseModel):
    variant_id: str = Field(max_length=255)
    chromosome: str = Field(max_length=10)
    position: int = Field(ge=1)
    ref: str = Field(max_length=500)
    alt: str = Field(max_length=500)
    type: str | None = Field(default=None, max_length=50)
    quality: float | None = None
    filter_status: str | None = Field(default=None, max_length=50)
    genome_id: uuid.UUID | None = None
    gene_id: uuid.UUID | None = None
    description: str | None = None


class VariantCreate(VariantBase):
    pass


class VariantUpdate(BaseModel):
    variant_id: str | None = Field(default=None, max_length=255)
    chromosome: str | None = Field(default=None, max_length=10)
    position: int | None = Field(default=None, ge=1)
    ref: str | None = Field(default=None, max_length=500)
    alt: str | None = Field(default=None, max_length=500)
    type: str | None = Field(default=None, max_length=50)
    quality: float | None = None
    filter_status: str | None = Field(default=None, max_length=50)
    genome_id: uuid.UUID | None = None
    gene_id: uuid.UUID | None = None
    description: str | None = None


class VariantResponse(VariantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
