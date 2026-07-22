from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateVariantError
from genomeai_api.models.variant import Variant
from genomeai_api.schemas.variant import VariantCreate, VariantUpdate


class VariantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: VariantCreate) -> Variant:
        variant = Variant(**data.model_dump())
        self._session.add(variant)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            orig = getattr(exc, "orig", None)
            if getattr(orig, "sqlstate", None) == "23505":
                raise DuplicateVariantError from None
            raise
        await self._session.refresh(variant)
        return variant

    async def get_by_id(self, variant_id: uuid.UUID) -> Variant | None:
        return await self._session.get(Variant, variant_id)

    async def list(self) -> list[Variant]:
        result = await self._session.execute(
            select(Variant).order_by(Variant.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, variant_id: uuid.UUID, data: VariantUpdate) -> Variant | None:
        variant = await self._session.get(Variant, variant_id)
        if variant is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(variant, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            orig = getattr(exc, "orig", None)
            if getattr(orig, "sqlstate", None) == "23505":
                raise DuplicateVariantError from None
            raise
        await self._session.refresh(variant)
        return variant

    async def delete(self, variant_id: uuid.UUID) -> bool:
        variant = await self._session.get(Variant, variant_id)
        if variant is None:
            return False
        await self._session.delete(variant)
        await self._session.commit()
        return True
