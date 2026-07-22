from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.gene import GeneRepository
from genomeai_api.schemas.gene import GeneCreate, GeneResponse, GeneUpdate
from genomeai_api.services.gene import GeneService

router = APIRouter(prefix="/genes", tags=["genes"])


async def _get_service(session: AsyncSession = Depends(get_db_session)) -> GeneService:
    repository = GeneRepository(session)
    return GeneService(repository)


@router.post("/", response_model=GeneResponse, status_code=status.HTTP_201_CREATED)
async def create_gene(
    data: GeneCreate,
    service: GeneService = Depends(_get_service),
) -> GeneResponse:
    return await service.create(data)


@router.get("/", response_model=list[GeneResponse])
async def list_genes(
    service: GeneService = Depends(_get_service),
) -> list[GeneResponse]:
    return await service.list()


@router.get("/{gene_id}", response_model=GeneResponse)
async def get_gene(
    gene_id: uuid.UUID,
    service: GeneService = Depends(_get_service),
) -> GeneResponse:
    result = await service.get_by_id(gene_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gene not found")
    return result


@router.patch("/{gene_id}", response_model=GeneResponse)
async def update_gene(
    gene_id: uuid.UUID,
    data: GeneUpdate,
    service: GeneService = Depends(_get_service),
) -> GeneResponse:
    result = await service.update(gene_id, data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gene not found")
    return result


@router.delete("/{gene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gene(
    gene_id: uuid.UUID,
    service: GeneService = Depends(_get_service),
) -> None:
    deleted = await service.delete(gene_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gene not found")
