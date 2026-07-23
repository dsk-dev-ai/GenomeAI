from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudyBase(BaseModel):
    study_id: str = Field(max_length=100)
    study_name: str = Field(max_length=255)
    study_type: str | None = Field(default=None, max_length=100)
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    organism: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=255)
    principal_investigator: str | None = Field(default=None, max_length=255)
    publication: str | None = Field(default=None, max_length=500)
    doi: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, max_length=50)
    genome_id: uuid.UUID | None = None
    dataset_id: uuid.UUID | None = None


class StudyCreate(StudyBase):
    pass


class StudyUpdate(BaseModel):
    study_id: str | None = Field(default=None, max_length=100)
    study_name: str | None = Field(default=None, max_length=255)
    study_type: str | None = Field(default=None, max_length=100)
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    organism: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=255)
    principal_investigator: str | None = Field(default=None, max_length=255)
    publication: str | None = Field(default=None, max_length=500)
    doi: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, max_length=50)
    genome_id: uuid.UUID | None = None
    dataset_id: uuid.UUID | None = None

    @field_validator("study_id", "study_name", mode="before")
    @classmethod
    def reject_null_non_nullable(cls, v: object) -> object:
        if v is None:
            raise ValueError("This field cannot be null")
        return v


class StudyResponse(StudyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
