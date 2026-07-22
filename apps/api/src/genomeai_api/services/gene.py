from __future__ import annotations

import uuid

from genomeai_api.repositories.gene import GeneRepository
from genomeai_api.schemas.gene import GeneCreate, GeneResponse, GeneUpdate


class GeneService:
    def __init__(self, repository: GeneRepository) -> None:
        self._repository = repository

    async def create(self, data: GeneCreate) -> GeneResponse:
        gene = await self._repository.create(data)
        return GeneResponse.model_validate(gene)

    async def get_by_id(self, gene_id: uuid.UUID) -> GeneResponse | None:
        gene = await self._repository.get_by_id(gene_id)
        if gene is None:
            return None
        return GeneResponse.model_validate(gene)

    async def list(self) -> list[GeneResponse]:
        genes = await self._repository.list()
        return [GeneResponse.model_validate(g) for g in genes]

    async def update(self, gene_id: uuid.UUID, data: GeneUpdate) -> GeneResponse | None:
        gene = await self._repository.update(gene_id, data)
        if gene is None:
            return None
        return GeneResponse.model_validate(gene)

    async def delete(self, gene_id: uuid.UUID) -> bool:
        return await self._repository.delete(gene_id)
