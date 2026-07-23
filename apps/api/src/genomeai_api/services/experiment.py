from __future__ import annotations

import uuid

from genomeai_api.repositories.experiment import ExperimentRepository
from genomeai_api.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
)


class ExperimentService:
    def __init__(self, repository: ExperimentRepository) -> None:
        self._repository = repository

    async def create(self, data: ExperimentCreate) -> ExperimentResponse:
        experiment = await self._repository.create(data)
        return ExperimentResponse.model_validate(experiment)

    async def get_by_id(
        self, experiment_id: uuid.UUID
    ) -> ExperimentResponse | None:
        experiment = await self._repository.get_by_id(experiment_id)
        if experiment is None:
            return None
        return ExperimentResponse.model_validate(experiment)

    async def list(self) -> list[ExperimentResponse]:
        experiments = await self._repository.list()
        return [ExperimentResponse.model_validate(e) for e in experiments]

    async def update(
        self, experiment_id: uuid.UUID, data: ExperimentUpdate
    ) -> ExperimentResponse | None:
        experiment = await self._repository.update(experiment_id, data)
        if experiment is None:
            return None
        return ExperimentResponse.model_validate(experiment)

    async def delete(self, experiment_id: uuid.UUID) -> bool:
        return await self._repository.delete(experiment_id)

    async def exists(self, experiment_id: uuid.UUID) -> bool:
        return await self._repository.exists(experiment_id)
