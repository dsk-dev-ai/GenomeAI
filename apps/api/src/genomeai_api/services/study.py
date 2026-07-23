from __future__ import annotations

import uuid

from genomeai_api.repositories.study import StudyRepository
from genomeai_api.schemas.study import (
    StudyCreate,
    StudyResponse,
    StudyUpdate,
)


class StudyService:
    def __init__(self, repository: StudyRepository) -> None:
        self._repository = repository

    async def create(self, data: StudyCreate) -> StudyResponse:
        study = await self._repository.create(data)
        return StudyResponse.model_validate(study)

    async def get_by_id(
        self, study_id: uuid.UUID
    ) -> StudyResponse | None:
        study = await self._repository.get_by_id(study_id)
        if study is None:
            return None
        return StudyResponse.model_validate(study)

    async def list(self) -> list[StudyResponse]:
        studies = await self._repository.list()
        return [StudyResponse.model_validate(s) for s in studies]

    async def update(
        self, study_id: uuid.UUID, data: StudyUpdate
    ) -> StudyResponse | None:
        study = await self._repository.update(study_id, data)
        if study is None:
            return None
        return StudyResponse.model_validate(study)

    async def delete(self, study_id: uuid.UUID) -> bool:
        return await self._repository.delete(study_id)

    async def exists(self, study_id: uuid.UUID) -> bool:
        return await self._repository.exists(study_id)
