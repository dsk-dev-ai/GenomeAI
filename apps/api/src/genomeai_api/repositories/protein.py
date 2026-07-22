from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import DuplicateProteinError
from genomeai_api.models.protein import Protein
from genomeai_api.schemas.protein import ProteinCreate, ProteinUpdate


class ProteinRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _handle_integrity_error(
        self, exc: IntegrityError
    ) -> None:
        orig = getattr(exc, "orig", None)
        if getattr(orig, "sqlstate", None) == "23505":
            raise DuplicateProteinError from None
        raise

    async def create(self, data: ProteinCreate) -> Protein:
        protein = Protein(**data.model_dump())
        self._session.add(protein)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(protein)
        return protein

    async def get_by_id(self, protein_id: uuid.UUID) -> Protein | None:
        return await self._session.get(Protein, protein_id)

    async def list(self) -> list[Protein]:
        result = await self._session.execute(
            select(Protein).order_by(Protein.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, protein_id: uuid.UUID, data: ProteinUpdate
    ) -> Protein | None:
        protein = await self._session.get(Protein, protein_id)
        if protein is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(protein, key, value)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            await self._handle_integrity_error(exc)
        await self._session.refresh(protein)
        return protein

    async def delete(self, protein_id: uuid.UUID) -> bool:
        protein = await self._session.get(Protein, protein_id)
        if protein is None:
            return False
        await self._session.delete(protein)
        await self._session.commit()
        return True

    async def exists(self, protein_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Protein.id).where(Protein.id == protein_id)
        )
        return result.scalars().one_or_none() is not None
