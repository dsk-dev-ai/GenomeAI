from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.models.protein import Protein
from genomeai_api.repositories.protein import ProteinRepository
from genomeai_api.routes.search import add_domain_search_routes
from genomeai_api.schemas.protein import (
    ProteinCreate,
    ProteinResponse,
    ProteinUpdate,
)
from genomeai_api.services.protein import ProteinService

router = APIRouter(prefix="/proteins", tags=["proteins"])


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProteinService:
    repository = ProteinRepository(session)
    return ProteinService(repository)


@router.post("/", response_model=ProteinResponse, status_code=status.HTTP_201_CREATED)
async def create_protein(
    data: ProteinCreate,
    service: ProteinService = Depends(_get_service),
) -> ProteinResponse:
    return await service.create(data)


@router.get("/", response_model=list[ProteinResponse])
async def list_proteins(
    service: ProteinService = Depends(_get_service),
) -> list[ProteinResponse]:
    return await service.list()


@router.get("/{protein_id}", response_model=ProteinResponse)
async def get_protein(
    protein_id: uuid.UUID,
    service: ProteinService = Depends(_get_service),
) -> ProteinResponse:
    result = await service.get_by_id(protein_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Protein not found"
        )
    return result


@router.patch("/{protein_id}", response_model=ProteinResponse)
async def update_protein(
    protein_id: uuid.UUID,
    data: ProteinUpdate,
    service: ProteinService = Depends(_get_service),
) -> ProteinResponse:
    result = await service.update(protein_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Protein not found"
        )
    return result


@router.delete("/{protein_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_protein(
    protein_id: uuid.UUID,
    service: ProteinService = Depends(_get_service),
) -> None:
    deleted = await service.delete(protein_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Protein not found"
        )


add_domain_search_routes(router, Protein, "proteins")
