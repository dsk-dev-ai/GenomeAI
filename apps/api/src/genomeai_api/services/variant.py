from __future__ import annotations

import uuid

from genomeai_api.repositories.variant import VariantRepository
from genomeai_api.schemas.variant import VariantCreate, VariantResponse, VariantUpdate


class VariantService:
    def __init__(self, repository: VariantRepository) -> None:
        self._repository = repository

    async def create(self, data: VariantCreate) -> VariantResponse:
        variant = await self._repository.create(data)
        return VariantResponse.model_validate(variant)

    async def get_by_id(self, variant_id: uuid.UUID) -> VariantResponse | None:
        variant = await self._repository.get_by_id(variant_id)
        if variant is None:
            return None
        return VariantResponse.model_validate(variant)

    async def list(self) -> list[VariantResponse]:
        variants = await self._repository.list()
        return [VariantResponse.model_validate(v) for v in variants]

    async def update(
        self, variant_id: uuid.UUID, data: VariantUpdate
    ) -> VariantResponse | None:
        variant = await self._repository.update(variant_id, data)
        if variant is None:
            return None
        return VariantResponse.model_validate(variant)

    async def delete(self, variant_id: uuid.UUID) -> bool:
        return await self._repository.delete(variant_id)
