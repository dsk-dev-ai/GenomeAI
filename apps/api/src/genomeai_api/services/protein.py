from __future__ import annotations

import uuid

from genomeai_api.repositories.protein import ProteinRepository
from genomeai_api.schemas.protein import (
    ProteinCreate,
    ProteinResponse,
    ProteinUpdate,
)


class ProteinService:
    def __init__(self, repository: ProteinRepository) -> None:
        self._repository = repository

    async def create(self, data: ProteinCreate) -> ProteinResponse:
        protein = await self._repository.create(data)
        return ProteinResponse.model_validate(protein)

    async def get_by_id(
        self, protein_id: uuid.UUID
    ) -> ProteinResponse | None:
        protein = await self._repository.get_by_id(protein_id)
        if protein is None:
            return None
        return ProteinResponse.model_validate(protein)

    async def list(self) -> list[ProteinResponse]:
        proteins = await self._repository.list()
        return [ProteinResponse.model_validate(p) for p in proteins]

    async def update(
        self, protein_id: uuid.UUID, data: ProteinUpdate
    ) -> ProteinResponse | None:
        protein = await self._repository.update(protein_id, data)
        if protein is None:
            return None
        return ProteinResponse.model_validate(protein)

    async def delete(self, protein_id: uuid.UUID) -> bool:
        return await self._repository.delete(protein_id)

    async def exists(self, protein_id: uuid.UUID) -> bool:
        return await self._repository.exists(protein_id)
