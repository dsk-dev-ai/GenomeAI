from __future__ import annotations

from genomeai_config import DatabaseSettings
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_engine(settings: DatabaseSettings) -> AsyncEngine:
    return create_async_engine(
        settings.url,
        pool_size=settings.max_size,
        max_overflow=10,
        pool_pre_ping=True,
        echo="localhost" in settings.url,
    )


async def dispose_engine(engine: AsyncEngine | None) -> None:
    if engine is None:
        return
    await engine.dispose()
