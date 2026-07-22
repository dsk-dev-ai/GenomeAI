from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.genome import GenomeRepository
from genomeai_api.schemas.genome import GenomeCreate, GenomeResponse, GenomeUpdate
from genomeai_api.services.genome import GenomeService

router = APIRouter(prefix="/genomes", tags=["genomes"])


async def _get_service(session: AsyncSession = Depends(get_db_session)) -> GenomeService:
    repository = GenomeRepository(session)
    return GenomeService(repository)


@router.post("/", response_model=GenomeResponse, status_code=status.HTTP_201_CREATED)
async def create_genome(
    data: GenomeCreate,
    service: GenomeService = Depends(_get_service),
) -> GenomeResponse:
    return await service.create(data)


@router.get("/", response_model=list[GenomeResponse])
async def list_genomes(
    service: GenomeService = Depends(_get_service),
) -> list[GenomeResponse]:
    return await service.list()


@router.get("/{genome_id}", response_model=GenomeResponse)
async def get_genome(
    genome_id: uuid.UUID,
    service: GenomeService = Depends(_get_service),
) -> GenomeResponse:
    result = await service.get_by_id(genome_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genome not found")
    return result


@router.patch("/{genome_id}", response_model=GenomeResponse)
async def update_genome(
    genome_id: uuid.UUID,
    data: GenomeUpdate,
    service: GenomeService = Depends(_get_service),
) -> GenomeResponse:
    result = await service.update(genome_id, data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genome not found")
    return result


@router.delete("/{genome_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genome(
    genome_id: uuid.UUID,
    service: GenomeService = Depends(_get_service),
) -> None:
    deleted = await service.delete(genome_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genome not found")
