from __future__ import annotations

import uuid

from genomeai_api.repositories.sample import SampleRepository
from genomeai_api.schemas.sample import SampleCreate, SampleResponse, SampleUpdate


class SampleService:
    def __init__(self, repository: SampleRepository) -> None:
        self._repository = repository

    async def create(self, data: SampleCreate) -> SampleResponse:
        sample = await self._repository.create(data)
        return SampleResponse.model_validate(sample)

    async def get_by_id(self, sample_id: uuid.UUID) -> SampleResponse | None:
        sample = await self._repository.get_by_id(sample_id)
        if sample is None:
            return None
        return SampleResponse.model_validate(sample)

    async def list(self) -> list[SampleResponse]:
        samples = await self._repository.list()
        return [SampleResponse.model_validate(s) for s in samples]

    async def update(self, sample_id: uuid.UUID, data: SampleUpdate) -> SampleResponse | None:
        sample = await self._repository.update(sample_id, data)
        if sample is None:
            return None
        return SampleResponse.model_validate(sample)

    async def delete(self, sample_id: uuid.UUID) -> bool:
        return await self._repository.delete(sample_id)
