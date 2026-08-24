"""Minimal REST API for workflows.

Phase 7.1: definitions, run initialization, inspection.
Phase 7.2: synchronous in-process run execution (no scheduler/queue).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunResponse,
    WorkflowUpdate,
)
from genomeai_api.services.workflow import WorkflowService
from genomeai_api.workflows.execution.engine import DAGExecutionEngine
from genomeai_api.workflows.execution.executor import PassthroughStepExecutor

router = APIRouter(prefix="/workflows", tags=["workflows"])


async def _get_service(session: AsyncSession = Depends(get_db_session)) -> WorkflowService:
    return WorkflowService(WorkflowRepository(session))


async def _get_engine(session: AsyncSession = Depends(get_db_session)) -> DAGExecutionEngine:
    """Synchronous in-process engine (Phase 7.2).

    The default executor is deterministic passthrough; real executors plug
    in here once they exist.
    """
    return DAGExecutionEngine(
        repository=WorkflowRepository(session),
        executor=PassthroughStepExecutor(),
    )


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowResponse:
    return await service.create_workflow(data)


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    service: WorkflowService = Depends(_get_service),
) -> list[WorkflowResponse]:
    return await service.list_workflows()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowResponse:
    return await service.get_workflow(workflow_id)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowResponse:
    result = await service.update_workflow(workflow_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )
    return result


@router.post(
    "/{workflow_id}/runs",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_run(
    workflow_id: uuid.UUID,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowRunResponse:
    return await service.create_run(workflow_id)


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_workflow_run(
    run_id: uuid.UUID,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowRunResponse:
    return await service.get_run(run_id)


@router.post("/runs/{run_id}/execute", response_model=WorkflowRunResponse)
async def execute_workflow_run(
    run_id: uuid.UUID,
    engine: DAGExecutionEngine = Depends(_get_engine),
) -> WorkflowRunResponse:
    """Executes one run synchronously, in-process.

    Phase 7.2 executes steps sequentially in topological order before
    responding; there is no background job or queue behind this endpoint.
    """
    run = await engine.execute_run(run_id)
    return WorkflowRunResponse.model_validate(run)
