from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectBase(BaseModel):
    project_id: str = Field(max_length=100)
    project_name: str = Field(max_length=255)
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    organization: str | None = Field(default=None, max_length=255)
    owner: str | None = Field(default=None, max_length=255)
    principal_investigator: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    genome_id: uuid.UUID | None = None
    study_id: uuid.UUID | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_id: str | None = Field(default=None, max_length=100)
    project_name: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    organization: str | None = Field(default=None, max_length=255)
    owner: str | None = Field(default=None, max_length=255)
    principal_investigator: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    genome_id: uuid.UUID | None = None
    study_id: uuid.UUID | None = None

    @field_validator("project_id", "project_name", mode="before")
    @classmethod
    def reject_null_non_nullable(cls, v: object) -> object:
        if v is None:
            raise ValueError("This field cannot be null")
        return v


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
