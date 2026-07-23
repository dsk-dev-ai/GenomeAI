from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatasetBase(BaseModel):
    dataset_id: str = Field(max_length=100)
    dataset_name: str = Field(max_length=255)
    dataset_type: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=255)
    organism: str | None = Field(default=None, max_length=255)
    version: str | None = Field(default=None, max_length=50)
    description: str | None = None
    sample_count: int | None = Field(default=None, ge=0)
    file_count: int | None = Field(default=None, ge=0)
    size_bytes: int | None = Field(default=None, ge=0)
    is_public: bool | None = None
    genome_id: uuid.UUID | None = None
    experiment_id: uuid.UUID | None = None


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    dataset_id: str | None = Field(default=None, max_length=100)
    dataset_name: str | None = Field(default=None, max_length=255)
    dataset_type: str | None = Field(default=None, max_length=100)
    source: str | None = Field(default=None, max_length=255)
    organism: str | None = Field(default=None, max_length=255)
    version: str | None = Field(default=None, max_length=50)
    description: str | None = None
    sample_count: int | None = Field(default=None, ge=0)
    file_count: int | None = Field(default=None, ge=0)
    size_bytes: int | None = Field(default=None, ge=0)
    is_public: bool | None = None
    genome_id: uuid.UUID | None = None
    experiment_id: uuid.UUID | None = None

    @field_validator("dataset_id", "dataset_name", mode="before")
    @classmethod
    def reject_null_non_nullable(cls, v: object) -> object:
        if v is None:
            raise ValueError("This field cannot be null")
        return v


class DatasetResponse(DatasetBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
