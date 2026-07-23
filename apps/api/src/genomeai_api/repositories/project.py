from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateProjectError, InvalidForeignKeyError
from genomeai_api.models.project import Project
from genomeai_api.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _handle_integrity_error(
        self, exc: IntegrityError
    ) -> None:
        orig = getattr(exc, "orig", None)
        sqlstate = getattr(orig, "sqlstate", None)
        if sqlstate == "23505":
            raise DuplicateProjectError from None
        if sqlstate == "23503":
            raise InvalidForeignKeyError from None
        raise

    async def create(self, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        self._session.add(project)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(project)
        return project

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        return await self._session.get(Project, project_id)

    async def list(self) -> list[Project]:
        result = await self._session.execute(
            select(Project).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, project_id: uuid.UUID, data: ProjectUpdate
    ) -> Project | None:
        project = await self._session.get(Project, project_id)
        if project is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(project)
        return project

    async def delete(self, project_id: uuid.UUID) -> bool:
        project = await self._session.get(Project, project_id)
        if project is None:
            return False
        await self._session.delete(project)
        await self._session.commit()
        return True

    async def exists(self, project_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Project.id).where(Project.id == project_id)
        )
        return result.scalars().one_or_none() is not None
