from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.transcript import TranscriptRepository
from genomeai_api.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
    TranscriptUpdate,
)
from genomeai_api.services.transcript import TranscriptService

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
) -> TranscriptService:
    repository = TranscriptRepository(session)
    return TranscriptService(repository)


@router.post("/", response_model=TranscriptResponse, status_code=status.HTTP_201_CREATED)
async def create_transcript(
    data: TranscriptCreate,
    service: TranscriptService = Depends(_get_service),
) -> TranscriptResponse:
    return await service.create(data)


@router.get("/", response_model=list[TranscriptResponse])
async def list_transcripts(
    service: TranscriptService = Depends(_get_service),
) -> list[TranscriptResponse]:
    return await service.list()


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: uuid.UUID,
    service: TranscriptService = Depends(_get_service),
) -> TranscriptResponse:
    result = await service.get_by_id(transcript_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found"
        )
    return result


@router.patch("/{transcript_id}", response_model=TranscriptResponse)
async def update_transcript(
    transcript_id: uuid.UUID,
    data: TranscriptUpdate,
    service: TranscriptService = Depends(_get_service),
) -> TranscriptResponse:
    result = await service.update(transcript_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found"
        )
    return result


@router.delete("/{transcript_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcript(
    transcript_id: uuid.UUID,
    service: TranscriptService = Depends(_get_service),
) -> None:
    deleted = await service.delete(transcript_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found"
        )
