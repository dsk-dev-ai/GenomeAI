from __future__ import annotations

import uuid

from genomeai_api.repositories.project import ProjectRepository
from genomeai_api.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def create(self, data: ProjectCreate) -> ProjectResponse:
        project = await self._repository.create(data)
        return ProjectResponse.model_validate(project)

    async def get_by_id(
        self, project_id: uuid.UUID
    ) -> ProjectResponse | None:
        project = await self._repository.get_by_id(project_id)
        if project is None:
            return None
        return ProjectResponse.model_validate(project)

    async def list(self) -> list[ProjectResponse]:
        projects = await self._repository.list()
        return [ProjectResponse.model_validate(p) for p in projects]

    async def update(
        self, project_id: uuid.UUID, data: ProjectUpdate
    ) -> ProjectResponse | None:
        project = await self._repository.update(project_id, data)
        if project is None:
            return None
        return ProjectResponse.model_validate(project)

    async def delete(self, project_id: uuid.UUID) -> bool:
        return await self._repository.delete(project_id)

    async def exists(self, project_id: uuid.UUID) -> bool:
        return await self._repository.exists(project_id)
