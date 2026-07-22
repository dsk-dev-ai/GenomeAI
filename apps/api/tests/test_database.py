from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from genomeai_api.database import Base, create_engine, create_session_factory, dispose_engine
from genomeai_config import DatabaseSettings
from sqlalchemy.ext.asyncio import AsyncEngine


def test_base_declarative() -> None:
    assert hasattr(Base, "metadata")


def test_create_engine() -> None:
    settings = DatabaseSettings(
        host="localhost",
        port=5432,
        user="test",
        password="test",
        database="testdb",
        min_size=1,
        max_size=5,
    )
    engine = create_engine(settings)
    assert isinstance(engine, AsyncEngine)
    assert str(engine.url).startswith("postgresql+asyncpg://")


@pytest.mark.asyncio
async def test_dispose_engine_none() -> None:
    await dispose_engine(None)


@pytest.mark.asyncio
async def test_dispose_engine() -> None:
    mock_engine = AsyncMock(spec=AsyncEngine)
    await dispose_engine(mock_engine)
    mock_engine.dispose.assert_awaited_once()


def test_create_session_factory_none() -> None:
    result = create_session_factory(None)
    assert result is None


def test_create_session_factory() -> None:
    settings = DatabaseSettings(
        host="localhost",
        port=5432,
        user="test",
        password="test",
        database="testdb",
        min_size=1,
        max_size=5,
    )
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    assert factory is not None
    assert callable(factory)


@pytest.mark.asyncio
async def test_get_db_session_not_initialized() -> None:
    from unittest.mock import MagicMock

    from genomeai_api.dependencies import get_db_session

    request = MagicMock()
    request.app.state.app_state.db_session_factory = None

    with pytest.raises(RuntimeError, match="database not initialized"):
        async for _ in get_db_session(request):
            pass
