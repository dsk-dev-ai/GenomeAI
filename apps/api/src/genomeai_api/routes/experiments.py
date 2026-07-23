from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.models.experiment import Experiment
from genomeai_api.repositories.experiment import ExperimentRepository
from genomeai_api.routes.search import add_domain_search_routes
from genomeai_api.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
)
from genomeai_api.services.experiment import ExperimentService

router = APIRouter(prefix="/experiments", tags=["experiments"])


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentService:
    repository = ExperimentRepository(session)
    return ExperimentService(repository)


@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ExperimentCreate,
    service: ExperimentService = Depends(_get_service),
) -> ExperimentResponse:
    return await service.create(data)


@router.get("/", response_model=list[ExperimentResponse])
async def list_experiments(
    service: ExperimentService = Depends(_get_service),
) -> list[ExperimentResponse]:
    return await service.list()


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    service: ExperimentService = Depends(_get_service),
) -> ExperimentResponse:
    result = await service.get_by_id(experiment_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    return result


@router.patch("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: uuid.UUID,
    data: ExperimentUpdate,
    service: ExperimentService = Depends(_get_service),
) -> ExperimentResponse:
    result = await service.update(experiment_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    return result


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: uuid.UUID,
    service: ExperimentService = Depends(_get_service),
) -> None:
    deleted = await service.delete(experiment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )


add_domain_search_routes(router, Experiment, "experiments")
