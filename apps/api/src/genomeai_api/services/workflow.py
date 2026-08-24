"""Service layer for the Workflow Foundation.

Owns definition validation (deterministic DAG checks) and run
initialization. The service must NOT execute workflow steps — runs are
created in the PENDING state and never advanced here.
"""

from __future__ import annotations

import uuid

from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunResponse,
    WorkflowUpdate,
)
from genomeai_api.workflows.dag import topological_order, validate_graph
from genomeai_api.workflows.errors import (
    WorkflowNotFoundError,
    WorkflowRunNotFoundError,
    WorkflowValidationError,
)


class WorkflowService:
    def __init__(self, repository: WorkflowRepository) -> None:
        self._repository = repository

    async def create_workflow(self, data: WorkflowCreate) -> WorkflowResponse:
        issues = validate_graph(
            step_names=[step.name for step in data.steps],
            edges=[(dep.from_step, dep.to_step) for dep in data.dependencies],
        )
        if issues:
            raise WorkflowValidationError(
                summary=(
                    f"Workflow '{data.name}' is not a valid DAG "
                    f"({len(issues)} issue{'s' if len(issues) != 1 else ''})"
                ),
                issues=[f"{issue.code}: {issue.message}" for issue in issues],
            )
        workflow = await self._repository.create(data)
        return WorkflowResponse.model_validate(workflow)

    async def get_workflow(self, workflow_id: uuid.UUID) -> WorkflowResponse:
        workflow = await self._repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)
        return WorkflowResponse.model_validate(workflow)

    async def list_workflows(self) -> list[WorkflowResponse]:
        workflows = await self._repository.list()
        return [WorkflowResponse.model_validate(w) for w in workflows]

    async def update_workflow(
        self, workflow_id: uuid.UUID, data: WorkflowUpdate
    ) -> WorkflowResponse | None:
        """Updates definition metadata; returns None when unknown to caller."""
        workflow = await self._repository.update_metadata(workflow_id, data)
        if workflow is None:
            return None
        return WorkflowResponse.model_validate(workflow)

    async def create_run(self, workflow_id: uuid.UUID) -> WorkflowRunResponse:
        """Requests one execution of a workflow.

        Initializes the run and its StepRuns in deterministic topological
        order, all PENDING. No execution happens in Phase 7.1.
        """
        workflow = await self._repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)

        names = [step.name for step in workflow.steps]
        id_by_name = {step.name: step.id for step in workflow.steps}
        name_by_id = {step.id: step.name for step in workflow.steps}
        name_edges = [
            (name_by_id[dep.from_step_id], name_by_id[dep.to_step_id])
            for dep in workflow.dependencies
        ]
        ordered_ids = [id_by_name[name] for name in topological_order(names, name_edges)]

        run = await self._repository.create_run(workflow_id, ordered_ids)
        return WorkflowRunResponse.model_validate(run)

    async def get_run(self, run_id: uuid.UUID) -> WorkflowRunResponse:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise WorkflowRunNotFoundError(run_id)
        return WorkflowRunResponse.model_validate(run)
