from __future__ import annotations

import uuid

from genomeai_api.repositories.genome import GenomeRepository
from genomeai_api.schemas.genome import GenomeCreate, GenomeResponse, GenomeUpdate


class GenomeService:
    def __init__(self, repository: GenomeRepository) -> None:
        self._repository = repository

    async def create(self, data: GenomeCreate) -> GenomeResponse:
        genome = await self._repository.create(data)
        return GenomeResponse.model_validate(genome)

    async def get_by_id(self, genome_id: uuid.UUID) -> GenomeResponse | None:
        genome = await self._repository.get_by_id(genome_id)
        if genome is None:
            return None
        return GenomeResponse.model_validate(genome)

    async def list(self) -> list[GenomeResponse]:
        genomes = await self._repository.list()
        return [GenomeResponse.model_validate(g) for g in genomes]

    async def update(self, genome_id: uuid.UUID, data: GenomeUpdate) -> GenomeResponse | None:
        genome = await self._repository.update(genome_id, data)
        if genome is None:
            return None
        return GenomeResponse.model_validate(genome)

    async def delete(self, genome_id: uuid.UUID) -> bool:
        return await self._repository.delete(genome_id)
