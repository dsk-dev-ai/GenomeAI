from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateDatasetError, InvalidForeignKeyError
from genomeai_api.models.dataset import Dataset
from genomeai_api.schemas.dataset import DatasetCreate, DatasetUpdate


class DatasetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _handle_integrity_error(
        self, exc: IntegrityError
    ) -> None:
        orig = getattr(exc, "orig", None)
        sqlstate = getattr(orig, "sqlstate", None)
        if sqlstate == "23505":
            raise DuplicateDatasetError from None
        if sqlstate == "23503":
            raise InvalidForeignKeyError from None
        raise

    async def create(self, data: DatasetCreate) -> Dataset:
        dataset = Dataset(**data.model_dump())
        self._session.add(dataset)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(dataset)
        return dataset

    async def get_by_id(self, dataset_id: uuid.UUID) -> Dataset | None:
        return await self._session.get(Dataset, dataset_id)

    async def list(self) -> list[Dataset]:
        result = await self._session.execute(
            select(Dataset).order_by(Dataset.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, dataset_id: uuid.UUID, data: DatasetUpdate
    ) -> Dataset | None:
        dataset = await self._session.get(Dataset, dataset_id)
        if dataset is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(dataset, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(dataset)
        return dataset

    async def delete(self, dataset_id: uuid.UUID) -> bool:
        dataset = await self._session.get(Dataset, dataset_id)
        if dataset is None:
            return False
        await self._session.delete(dataset)
        await self._session.commit()
        return True

    async def exists(self, dataset_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Dataset.id).where(Dataset.id == dataset_id)
        )
        return result.scalars().one_or_none() is not None
