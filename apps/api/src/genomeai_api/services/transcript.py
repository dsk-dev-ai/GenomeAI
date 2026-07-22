from __future__ import annotations

import uuid

from genomeai_api.repositories.transcript import TranscriptRepository
from genomeai_api.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
    TranscriptUpdate,
)


class TranscriptService:
    def __init__(self, repository: TranscriptRepository) -> None:
        self._repository = repository

    async def create(self, data: TranscriptCreate) -> TranscriptResponse:
        transcript = await self._repository.create(data)
        return TranscriptResponse.model_validate(transcript)

    async def get_by_id(
        self, transcript_id: uuid.UUID
    ) -> TranscriptResponse | None:
        transcript = await self._repository.get_by_id(transcript_id)
        if transcript is None:
            return None
        return TranscriptResponse.model_validate(transcript)

    async def list(self) -> list[TranscriptResponse]:
        transcripts = await self._repository.list()
        return [TranscriptResponse.model_validate(t) for t in transcripts]

    async def update(
        self, transcript_id: uuid.UUID, data: TranscriptUpdate
    ) -> TranscriptResponse | None:
        transcript = await self._repository.update(transcript_id, data)
        if transcript is None:
            return None
        return TranscriptResponse.model_validate(transcript)

    async def delete(self, transcript_id: uuid.UUID) -> bool:
        return await self._repository.delete(transcript_id)
