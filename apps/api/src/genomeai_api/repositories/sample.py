from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateSampleError
from genomeai_api.models.sample import Sample
from genomeai_api.schemas.sample import SampleCreate, SampleUpdate


class SampleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: SampleCreate) -> Sample:
        sample = Sample(**data.model_dump())
        self._session.add(sample)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            orig = getattr(exc, "orig", None)
            if getattr(orig, "sqlstate", None) == "23505":
                raise DuplicateSampleError from None
            raise
        await self._session.refresh(sample)
        return sample

    async def get_by_id(self, sample_id: uuid.UUID) -> Sample | None:
        return await self._session.get(Sample, sample_id)

    async def list(self) -> list[Sample]:
        result = await self._session.execute(select(Sample).order_by(Sample.created_at.desc()))
        return list(result.scalars().all())

    async def update(self, sample_id: uuid.UUID, data: SampleUpdate) -> Sample | None:
        sample = await self._session.get(Sample, sample_id)
        if sample is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(sample, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            orig = getattr(exc, "orig", None)
            if getattr(orig, "sqlstate", None) == "23505":
                raise DuplicateSampleError from None
            raise
        await self._session.refresh(sample)
        return sample

    async def delete(self, sample_id: uuid.UUID) -> bool:
        sample = await self._session.get(Sample, sample_id)
        if sample is None:
            return False
        await self._session.delete(sample)
        await self._session.commit()
        return True
