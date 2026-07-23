from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.dataset import DatasetRepository
from genomeai_api.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
)
from genomeai_api.services.dataset import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
) -> DatasetService:
    repository = DatasetRepository(session)
    return DatasetService(repository)


@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    data: DatasetCreate,
    service: DatasetService = Depends(_get_service),
) -> DatasetResponse:
    return await service.create(data)


@router.get("/", response_model=list[DatasetResponse])
async def list_datasets(
    service: DatasetService = Depends(_get_service),
) -> list[DatasetResponse]:
    return await service.list()


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    service: DatasetService = Depends(_get_service),
) -> DatasetResponse:
    result = await service.get_by_id(dataset_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    return result


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: uuid.UUID,
    data: DatasetUpdate,
    service: DatasetService = Depends(_get_service),
) -> DatasetResponse:
    result = await service.update(dataset_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    return result


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: uuid.UUID,
    service: DatasetService = Depends(_get_service),
) -> None:
    deleted = await service.delete(dataset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
