"""Pydantic schemas for workflow schedules (Phase 7.3)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from genomeai_api.workflows.types import ScheduleType


class ScheduleCreate(BaseModel):
    """Submission payload for a new schedule on an existing workflow.

    `once` schedules require a timezone-aware `run_at` and no expression;
    `recurring` schedules require a standard 5-field cron `expression`.
    Domain validation (cron syntax, timezone names) happens in the
    scheduler service so API errors carry the full issue list.
    """

    schedule_type: ScheduleType = ScheduleType.ONCE
    run_at: datetime | None = None
    expression: str | None = Field(default=None, max_length=255)
    timezone_name: str = Field(default="UTC", min_length=1, max_length=64)


class ScheduleUpdate(BaseModel):
    """Partial spec update; lifecycle state changes use dedicated endpoints."""

    run_at: datetime | None = None
    expression: str | None = Field(default=None, max_length=255)
    timezone_name: str | None = Field(default=None, min_length=1, max_length=64)


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    schedule_type: ScheduleType
    expression: str | None
    run_at: datetime | None
    timezone_name: str
    state: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SchedulerEvaluationResponse(BaseModel):
    """Result of one deterministic scheduler evaluation pass."""

    evaluated_at: datetime
    created_runs: list[uuid.UUID]
    skipped_duplicates: int
