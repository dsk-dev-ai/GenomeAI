from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.project import ProjectRepository
from genomeai_api.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from genomeai_api.services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectService:
    repository = ProjectRepository(session)
    return ProjectService(repository)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(_get_service),
) -> ProjectResponse:
    return await service.create(data)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    service: ProjectService = Depends(_get_service),
) -> list[ProjectResponse]:
    return await service.list()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    service: ProjectService = Depends(_get_service),
) -> ProjectResponse:
    result = await service.get_by_id(project_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return result


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    service: ProjectService = Depends(_get_service),
) -> ProjectResponse:
    result = await service.update(project_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return result


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    service: ProjectService = Depends(_get_service),
) -> None:
    deleted = await service.delete(project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
