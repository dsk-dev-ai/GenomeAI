from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from genomeai_api.state import AppState


def create_session_factory(
    engine: AsyncEngine | None,
) -> async_sessionmaker[AsyncSession] | None:
    if engine is None:
        return None
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    state: AppState = request.app.state.app_state
    if state.db_session_factory is None:
        raise RuntimeError("database not initialized")
    async with state.db_session_factory() as session:
        yield session
