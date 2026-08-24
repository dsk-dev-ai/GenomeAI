from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from genomeai_api.workflows.types import RunState, WorkflowStatus


class WorkflowStepSpec(BaseModel):
    """One step in a submitted workflow definition."""

    name: str = Field(min_length=1, max_length=255)
    step_type: str = Field(min_length=1, max_length=100)
    configuration: dict[str, Any] = Field(default_factory=dict)
    position: int = Field(default=0, ge=0)


class WorkflowDependencySpec(BaseModel):
    """One directed edge `from_step → to_step`, referenced by step name."""

    from_step: str = Field(min_length=1, max_length=255)
    to_step: str = Field(min_length=1, max_length=255)


class WorkflowCreate(BaseModel):
    """Submission payload for a new workflow definition."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    version: str = Field(default="0.1.0", min_length=1, max_length=50)
    steps: list[WorkflowStepSpec] = Field(min_length=1)
    dependencies: list[WorkflowDependencySpec] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    """Partial update of workflow definition metadata (not its DAG)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    version: str | None = Field(default=None, min_length=1, max_length=50)
    status: WorkflowStatus | None = None


class WorkflowStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    step_type: str
    configuration: dict[str, Any]
    position: int


class WorkflowDependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_step_id: uuid.UUID
    to_step_id: uuid.UUID


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
    steps: list[WorkflowStepResponse]
    dependencies: list[WorkflowDependencyResponse]


class StepRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    step_id: uuid.UUID
    state: RunState
    position: int
    started_at: datetime | None
    finished_at: datetime | None


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    state: RunState
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
    step_runs: list[StepRunResponse]
