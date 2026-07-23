from __future__ import annotations

import uuid

from genomeai_api.repositories.dataset import DatasetRepository
from genomeai_api.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
)


class DatasetService:
    def __init__(self, repository: DatasetRepository) -> None:
        self._repository = repository

    async def create(self, data: DatasetCreate) -> DatasetResponse:
        dataset = await self._repository.create(data)
        return DatasetResponse.model_validate(dataset)

    async def get_by_id(
        self, dataset_id: uuid.UUID
    ) -> DatasetResponse | None:
        dataset = await self._repository.get_by_id(dataset_id)
        if dataset is None:
            return None
        return DatasetResponse.model_validate(dataset)

    async def list(self) -> list[DatasetResponse]:
        datasets = await self._repository.list()
        return [DatasetResponse.model_validate(d) for d in datasets]

    async def update(
        self, dataset_id: uuid.UUID, data: DatasetUpdate
    ) -> DatasetResponse | None:
        dataset = await self._repository.update(dataset_id, data)
        if dataset is None:
            return None
        return DatasetResponse.model_validate(dataset)

    async def delete(self, dataset_id: uuid.UUID) -> bool:
        return await self._repository.delete(dataset_id)

    async def exists(self, dataset_id: uuid.UUID) -> bool:
        return await self._repository.exists(dataset_id)
