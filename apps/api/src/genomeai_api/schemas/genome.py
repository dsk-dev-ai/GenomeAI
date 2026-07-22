from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenomeBase(BaseModel):
    accession: str
    organism: str
    assembly: str | None = None
    source: str | None = None
    description: str | None = None


class GenomeCreate(GenomeBase):
    pass


class GenomeUpdate(BaseModel):
    accession: str | None = None
    organism: str | None = None
    assembly: str | None = None
    source: str | None = None
    description: str | None = None


class GenomeResponse(GenomeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
