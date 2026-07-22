from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from genomeai_config import load_settings
from genomeai_logging import configure_logging, get_logger

from genomeai_api.cache import create_redis, shutdown_redis, verify_redis
from genomeai_api.database import create_engine, create_session_factory, dispose_engine
from genomeai_api.routes.health import router as health_router
from genomeai_api.state import AppState


async def init_db(state: AppState) -> None:
    engine = create_engine(state.settings.database)
    state.db_engine = engine
    state.db_session_factory = create_session_factory(engine)


async def init_cache(state: AppState) -> None:
    client = create_redis(state.settings.redis)
    ok = await verify_redis(client)
    if ok:
        state.redis = client
        state.logger.info("redis connected")
    else:
        state.logger.warning("redis not available")


async def shutdown_db(state: AppState) -> None:
    await dispose_engine(state.db_engine)
    state.db_engine = None
    state.db_session_factory = None


async def shutdown_cache(state: AppState) -> None:
    await shutdown_redis(state.redis)
    state.redis = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = load_settings()
    state = AppState(
        settings=settings,
        logger=get_logger(settings.service_name),
    )
    configure_logging(
        level=state.settings.log_level.value,
        json_format=state.settings.logging.json_format,
    )
    app.state.app_state = state
    state.logger.info("starting api")
    try:
        await init_db(state)
        state.logger.info("database engine created")
    except Exception as exc:
        state.logger.warning("database not available: %s", exc)
    try:
        await init_cache(state)
    except Exception:
        state.logger.warning("redis not available")
    yield
    await shutdown_cache(state)
    await shutdown_db(state)
    state.logger.info("stopping api")


app = FastAPI(
    title="GenomeAI API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)


def run() -> None:
    import uvicorn

    uvicorn.run(
        "genomeai_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
