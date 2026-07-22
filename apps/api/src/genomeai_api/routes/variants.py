from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.variant import VariantRepository
from genomeai_api.schemas.variant import VariantCreate, VariantResponse, VariantUpdate
from genomeai_api.services.variant import VariantService

router = APIRouter(prefix="/variants", tags=["variants"])


async def _get_service(session: AsyncSession = Depends(get_db_session)) -> VariantService:
    repository = VariantRepository(session)
    return VariantService(repository)


@router.post("/", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    data: VariantCreate,
    service: VariantService = Depends(_get_service),
) -> VariantResponse:
    return await service.create(data)


@router.get("/", response_model=list[VariantResponse])
async def list_variants(
    service: VariantService = Depends(_get_service),
) -> list[VariantResponse]:
    return await service.list()


@router.get("/{variant_id}", response_model=VariantResponse)
async def get_variant(
    variant_id: uuid.UUID,
    service: VariantService = Depends(_get_service),
) -> VariantResponse:
    result = await service.get_by_id(variant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    return result


@router.patch("/{variant_id}", response_model=VariantResponse)
async def update_variant(
    variant_id: uuid.UUID,
    data: VariantUpdate,
    service: VariantService = Depends(_get_service),
) -> VariantResponse:
    result = await service.update(variant_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found"
        )
    return result


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: uuid.UUID,
    service: VariantService = Depends(_get_service),
) -> None:
    deleted = await service.delete(variant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
