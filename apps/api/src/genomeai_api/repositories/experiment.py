from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateExperimentError, InvalidForeignKeyError
from genomeai_api.models.experiment import Experiment
from genomeai_api.schemas.experiment import ExperimentCreate, ExperimentUpdate


class ExperimentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _handle_integrity_error(
        self, exc: IntegrityError
    ) -> None:
        orig = getattr(exc, "orig", None)
        sqlstate = getattr(orig, "sqlstate", None)
        if sqlstate == "23505":
            raise DuplicateExperimentError from None
        if sqlstate == "23503":
            raise InvalidForeignKeyError from None
        raise

    async def create(self, data: ExperimentCreate) -> Experiment:
        experiment = Experiment(**data.model_dump())
        self._session.add(experiment)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(experiment)
        return experiment

    async def get_by_id(self, experiment_id: uuid.UUID) -> Experiment | None:
        return await self._session.get(Experiment, experiment_id)

    async def list(self) -> list[Experiment]:
        result = await self._session.execute(
            select(Experiment).order_by(Experiment.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, experiment_id: uuid.UUID, data: ExperimentUpdate
    ) -> Experiment | None:
        experiment = await self._session.get(Experiment, experiment_id)
        if experiment is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(experiment, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(experiment)
        return experiment

    async def delete(self, experiment_id: uuid.UUID) -> bool:
        experiment = await self._session.get(Experiment, experiment_id)
        if experiment is None:
            return False
        await self._session.delete(experiment)
        await self._session.commit()
        return True

    async def exists(self, experiment_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Experiment.id).where(Experiment.id == experiment_id)
        )
        return result.scalars().one_or_none() is not None
