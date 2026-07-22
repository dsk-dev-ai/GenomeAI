from __future__ import annotations

import logging
from dataclasses import dataclass, field

from genomeai_config import Settings
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


@dataclass
class AppState:
    settings: Settings
    logger: logging.Logger = field(compare=False)
    db_engine: AsyncEngine | None = field(default=None, compare=False)
    db_session_factory: async_sessionmaker[AsyncSession] | None = field(default=None, compare=False)
    redis: Redis | None = field(default=None, compare=False)
