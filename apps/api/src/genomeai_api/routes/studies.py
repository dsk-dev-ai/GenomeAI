from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.models.study import Study
from genomeai_api.repositories.study import StudyRepository
from genomeai_api.routes.search import add_domain_search_routes
from genomeai_api.schemas.study import (
    StudyCreate,
    StudyResponse,
    StudyUpdate,
)
from genomeai_api.services.study import StudyService

router = APIRouter(prefix="/studies", tags=["studies"])


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
) -> StudyService:
    repository = StudyRepository(session)
    return StudyService(repository)


@router.post("/", response_model=StudyResponse, status_code=status.HTTP_201_CREATED)
async def create_study(
    data: StudyCreate,
    service: StudyService = Depends(_get_service),
) -> StudyResponse:
    return await service.create(data)


@router.get("/", response_model=list[StudyResponse])
async def list_studies(
    service: StudyService = Depends(_get_service),
) -> list[StudyResponse]:
    return await service.list()


@router.get("/{study_id}", response_model=StudyResponse)
async def get_study(
    study_id: uuid.UUID,
    service: StudyService = Depends(_get_service),
) -> StudyResponse:
    result = await service.get_by_id(study_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study not found"
        )
    return result


@router.patch("/{study_id}", response_model=StudyResponse)
async def update_study(
    study_id: uuid.UUID,
    data: StudyUpdate,
    service: StudyService = Depends(_get_service),
) -> StudyResponse:
    result = await service.update(study_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study not found"
        )
    return result


@router.delete("/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study(
    study_id: uuid.UUID,
    service: StudyService = Depends(_get_service),
) -> None:
    deleted = await service.delete(study_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Study not found"
        )


add_domain_search_routes(router, Study, "studies")
