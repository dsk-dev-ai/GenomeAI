from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExperimentBase(BaseModel):
    experiment_id: str = Field(max_length=100)
    experiment_name: str = Field(max_length=255)
    experiment_type: str | None = Field(default=None, max_length=100)
    platform: str | None = Field(default=None, max_length=100)
    technology: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    organism: str | None = Field(default=None, max_length=255)
    laboratory: str | None = Field(default=None, max_length=255)
    researcher: str | None = Field(default=None, max_length=255)
    sample_id: uuid.UUID | None = None
    genome_id: uuid.UUID | None = None
    description: str | None = None


class ExperimentCreate(ExperimentBase):
    pass


class ExperimentUpdate(BaseModel):
    experiment_id: str | None = Field(default=None, max_length=100)
    experiment_name: str | None = Field(default=None, max_length=255)
    experiment_type: str | None = Field(default=None, max_length=100)
    platform: str | None = Field(default=None, max_length=100)
    technology: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    organism: str | None = Field(default=None, max_length=255)
    laboratory: str | None = Field(default=None, max_length=255)
    researcher: str | None = Field(default=None, max_length=255)
    sample_id: uuid.UUID | None = None
    genome_id: uuid.UUID | None = None
    description: str | None = None

    @field_validator("experiment_id", "experiment_name", mode="before")
    @classmethod
    def reject_null_non_nullable(cls, v: object) -> object:
        if v is None:
            raise ValueError("This field cannot be null")
        return v


class ExperimentResponse(ExperimentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
