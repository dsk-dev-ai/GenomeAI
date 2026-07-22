from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

MAX_LENGTH_SAMPLE_ID: int = 100
MAX_LENGTH_SAMPLE_NAME: int = 255
MAX_LENGTH_ORGANISM: int = 255
MAX_LENGTH_TISSUE: int = 255
MAX_LENGTH_CELL_TYPE: int = 255
MAX_LENGTH_DISEASE: int = 255
MAX_LENGTH_PHENOTYPE: int = 255
MAX_LENGTH_SEX: int = 20
MAX_LENGTH_AGE: int = 50


class SampleBase(BaseModel):
    sample_id: str = Field(max_length=MAX_LENGTH_SAMPLE_ID)
    sample_name: str = Field(max_length=MAX_LENGTH_SAMPLE_NAME)
    organism: str = Field(max_length=MAX_LENGTH_ORGANISM)
    tissue: str | None = Field(default=None, max_length=MAX_LENGTH_TISSUE)
    cell_type: str | None = Field(default=None, max_length=MAX_LENGTH_CELL_TYPE)
    disease: str | None = Field(default=None, max_length=MAX_LENGTH_DISEASE)
    phenotype: str | None = Field(default=None, max_length=MAX_LENGTH_PHENOTYPE)
    sex: str | None = Field(default=None, max_length=MAX_LENGTH_SEX)
    age: str | None = Field(default=None, max_length=MAX_LENGTH_AGE)
    genome_id: uuid.UUID | None = None
    description: str | None = None


class SampleCreate(SampleBase):
    pass


class SampleUpdate(BaseModel):
    sample_id: str | None = Field(default=None, max_length=MAX_LENGTH_SAMPLE_ID)
    sample_name: str | None = Field(default=None, max_length=MAX_LENGTH_SAMPLE_NAME)
    organism: str | None = Field(default=None, max_length=MAX_LENGTH_ORGANISM)
    tissue: str | None = Field(default=None, max_length=MAX_LENGTH_TISSUE)
    cell_type: str | None = Field(default=None, max_length=MAX_LENGTH_CELL_TYPE)
    disease: str | None = Field(default=None, max_length=MAX_LENGTH_DISEASE)
    phenotype: str | None = Field(default=None, max_length=MAX_LENGTH_PHENOTYPE)
    sex: str | None = Field(default=None, max_length=MAX_LENGTH_SEX)
    age: str | None = Field(default=None, max_length=MAX_LENGTH_AGE)
    genome_id: uuid.UUID | None = None
    description: str | None = None


class SampleResponse(SampleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
