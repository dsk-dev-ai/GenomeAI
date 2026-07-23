from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateStudyError, InvalidForeignKeyError
from genomeai_api.models.study import Study
from genomeai_api.schemas.study import StudyCreate, StudyUpdate


class StudyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _handle_integrity_error(
        self, exc: IntegrityError
    ) -> None:
        orig = getattr(exc, "orig", None)
        sqlstate = getattr(orig, "sqlstate", None)
        if sqlstate == "23505":
            raise DuplicateStudyError from None
        if sqlstate == "23503":
            raise InvalidForeignKeyError from None
        raise

    async def create(self, data: StudyCreate) -> Study:
        study = Study(**data.model_dump())
        self._session.add(study)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(study)
        return study

    async def get_by_id(self, study_id: uuid.UUID) -> Study | None:
        return await self._session.get(Study, study_id)

    async def list(self) -> list[Study]:
        result = await self._session.execute(
            select(Study).order_by(Study.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, study_id: uuid.UUID, data: StudyUpdate
    ) -> Study | None:
        study = await self._session.get(Study, study_id)
        if study is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(study, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(study)
        return study

    async def delete(self, study_id: uuid.UUID) -> bool:
        study = await self._session.get(Study, study_id)
        if study is None:
            return False
        await self._session.delete(study)
        await self._session.commit()
        return True

    async def exists(self, study_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Study.id).where(Study.id == study_id)
        )
        return result.scalars().one_or_none() is not None
