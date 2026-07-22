from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateGenomeAccessionError
from genomeai_api.models.genome import Genome
from genomeai_api.schemas.genome import GenomeCreate, GenomeUpdate


class GenomeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: GenomeCreate) -> Genome:
        genome = Genome(**data.model_dump())
        self._session.add(genome)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise DuplicateGenomeAccessionError from None
        await self._session.refresh(genome)
        return genome

    async def get_by_id(self, genome_id: uuid.UUID) -> Genome | None:
        return await self._session.get(Genome, genome_id)

    async def list(self) -> list[Genome]:
        result = await self._session.execute(select(Genome).order_by(Genome.created_at.desc()))
        return list(result.scalars().all())

    async def update(self, genome_id: uuid.UUID, data: GenomeUpdate) -> Genome | None:
        genome = await self._session.get(Genome, genome_id)
        if genome is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(genome, key, value)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise DuplicateGenomeAccessionError from None
        await self._session.refresh(genome)
        return genome

    async def delete(self, genome_id: uuid.UUID) -> bool:
        genome = await self._session.get(Genome, genome_id)
        if genome is None:
            return False
        await self._session.delete(genome)
        await self._session.commit()
        return True
