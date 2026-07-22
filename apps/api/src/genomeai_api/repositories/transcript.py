from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateTranscriptError
from genomeai_api.models.transcript import Transcript
from genomeai_api.schemas.transcript import TranscriptCreate, TranscriptUpdate


class TranscriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _handle_integrity_error(
        self, exc: IntegrityError
    ) -> None:
        orig = getattr(exc, "orig", None)
        if getattr(orig, "sqlstate", None) == "23505":
            raise DuplicateTranscriptError from None
        raise

    async def create(self, data: TranscriptCreate) -> Transcript:
        transcript = Transcript(**data.model_dump())
        self._session.add(transcript)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(transcript)
        return transcript

    async def get_by_id(self, transcript_id: uuid.UUID) -> Transcript | None:
        return await self._session.get(Transcript, transcript_id)

    async def list(self) -> list[Transcript]:
        result = await self._session.execute(
            select(Transcript).order_by(Transcript.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, transcript_id: uuid.UUID, data: TranscriptUpdate
    ) -> Transcript | None:
        transcript = await self._session.get(Transcript, transcript_id)
        if transcript is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(transcript, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(transcript)
        return transcript

    async def delete(self, transcript_id: uuid.UUID) -> bool:
        transcript = await self._session.get(Transcript, transcript_id)
        if transcript is None:
            return False
        await self._session.delete(transcript)
        await self._session.commit()
        return True
