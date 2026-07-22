from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateGeneError
from genomeai_api.models.gene import Gene
from genomeai_api.schemas.gene import GeneCreate, GeneUpdate


class GeneRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: GeneCreate) -> Gene:
        gene = Gene(**data.model_dump())
        self._session.add(gene)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            orig = getattr(exc, "orig", None)
            if getattr(orig, "sqlstate", None) == "23505":
                raise DuplicateGeneError from None
            raise
        await self._session.refresh(gene)
        return gene

    async def get_by_id(self, gene_id: uuid.UUID) -> Gene | None:
        return await self._session.get(Gene, gene_id)

    async def list(self) -> list[Gene]:
        result = await self._session.execute(select(Gene).order_by(Gene.created_at.desc()))
        return list(result.scalars().all())

    async def update(self, gene_id: uuid.UUID, data: GeneUpdate) -> Gene | None:
        gene = await self._session.get(Gene, gene_id)
        if gene is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(gene, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            orig = getattr(exc, "orig", None)
            if getattr(orig, "sqlstate", None) == "23505":
                raise DuplicateGeneError from None
            raise
        await self._session.refresh(gene)
        return gene

    async def delete(self, gene_id: uuid.UUID) -> bool:
        gene = await self._session.get(Gene, gene_id)
        if gene is None:
            return False
        await self._session.delete(gene)
        await self._session.commit()
        return True
