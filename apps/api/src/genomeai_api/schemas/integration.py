from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from genomeai_api.integration.types import EntityType, JobState


def _validate_http_url(value: str) -> str:
    if not value.startswith(("http://", "https://")):
        raise ValueError("api_base_url must use http:// or https://")
    return value


class DataSourceCreate(BaseModel):
    """Admin payload registering an external data source."""

    source_id: str = Field(max_length=100, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    provider: str = Field(max_length=255)
    display_name: str = Field(max_length=255)
    source_type: str = Field(default="other", max_length=50)
    api_base_url: str = Field(max_length=500)
    documentation_url: str | None = Field(default=None, max_length=500)
    auth_mode: str = Field(default="none", max_length=50)
    credential_ref: str | None = Field(default=None, max_length=255)
    rate_limit: dict[str, Any] = Field(default_factory=dict)
    license_info: dict[str, Any] = Field(default_factory=dict)
    access_mode: str = Field(default="live", max_length=50)
    enabled: bool = True
    feature_flags: dict[str, Any] = Field(default_factory=dict)

    @field_validator("api_base_url")
    @classmethod
    def _check_base_url(cls, value: str) -> str:
        return _validate_http_url(value)


class DataSourceUpdate(BaseModel):
    """Partial admin update for a registered source."""

    display_name: str | None = Field(default=None, max_length=255)
    documentation_url: str | None = Field(default=None, max_length=500)
    credential_ref: str | None = Field(default=None, max_length=255)
    rate_limit: dict[str, Any] | None = None
    license_info: dict[str, Any] | None = None
    feature_flags: dict[str, Any] | None = None
    enabled: bool | None = None


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: str
    provider: str
    display_name: str
    source_type: str
    api_base_url: str
    documentation_url: str | None
    auth_mode: str
    credential_ref: str | None
    rate_limit: dict[str, Any]
    license_info: dict[str, Any]
    access_mode: str
    source_version: str | None
    last_synced_at: datetime | None
    sync_status: str
    enabled: bool
    feature_flags: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ExternalIdentifierCreate(BaseModel):
    """Maps one external record id to a GenomeAI internal entity."""

    source_id: str = Field(max_length=100)
    external_id: str = Field(min_length=1, max_length=255)
    entity_type: EntityType
    genomeai_entity_id: uuid.UUID
    namespace: str | None = Field(default=None, max_length=100)
    version: str | None = Field(default=None, max_length=100)


class ExternalIdentifierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: str
    external_id: str
    entity_type: str
    genomeai_entity_id: uuid.UUID
    namespace: str | None
    version: str | None
    provenance_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ConnectorHealthResponse(BaseModel):
    """Result of asking a registered connector to health-check its source."""

    source_id: str
    ok: bool
    checked_at: datetime
    message: str
    latency_ms: int | None


class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: str
    state: JobState
    started_at: datetime | None
    finished_at: datetime | None
    records_received: int
    records_succeeded: int
    records_failed: int
    error_message: str | None
    created_at: datetime


class IngestionJobCreate(BaseModel):
    """Creates a pending ingestion job for one registered source."""

    source_id: str = Field(min_length=1, max_length=100)


class IngestionJobComplete(BaseModel):
    """Reports completion counts for an ingestion job."""

    received: int = Field(ge=0)
    succeeded: int = Field(ge=0)


class IngestionJobFailure(BaseModel):
    """Reports a failed ingestion job (message is required)."""

    received: int = Field(ge=0)
    failed: int = Field(ge=0)
    error_message: str = Field(min_length=1)
