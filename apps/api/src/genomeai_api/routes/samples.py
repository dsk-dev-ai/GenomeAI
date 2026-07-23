from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.models.sample import Sample
from genomeai_api.repositories.sample import SampleRepository
from genomeai_api.routes.search import add_domain_search_routes
from genomeai_api.schemas.sample import SampleCreate, SampleResponse, SampleUpdate
from genomeai_api.services.sample import SampleService

router = APIRouter(prefix="/samples", tags=["samples"])


async def _get_service(session: AsyncSession = Depends(get_db_session)) -> SampleService:
    repository = SampleRepository(session)
    return SampleService(repository)


@router.post("/", response_model=SampleResponse, status_code=status.HTTP_201_CREATED)
async def create_sample(
    data: SampleCreate,
    service: SampleService = Depends(_get_service),
) -> SampleResponse:
    return await service.create(data)


@router.get("/", response_model=list[SampleResponse])
async def list_samples(
    service: SampleService = Depends(_get_service),
) -> list[SampleResponse]:
    return await service.list()


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(
    sample_id: uuid.UUID,
    service: SampleService = Depends(_get_service),
) -> SampleResponse:
    result = await service.get_by_id(sample_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return result


@router.patch("/{sample_id}", response_model=SampleResponse)
async def update_sample(
    sample_id: uuid.UUID,
    data: SampleUpdate,
    service: SampleService = Depends(_get_service),
) -> SampleResponse:
    result = await service.update(sample_id, data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return result


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sample(
    sample_id: uuid.UUID,
    service: SampleService = Depends(_get_service),
) -> None:
    deleted = await service.delete(sample_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")


add_domain_search_routes(router, Sample, "samples")
