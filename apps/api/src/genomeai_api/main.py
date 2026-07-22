from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from genomeai_config import load_settings
from genomeai_logging import configure_logging, get_logger

from genomeai_api.routes.health import router as health_router
from genomeai_api.state import AppState


def create_app_state() -> AppState:
    settings = load_settings()
    return AppState(
        settings=settings,
        logger=get_logger(settings.service_name),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    state = create_app_state()
    configure_logging(
        level=state.settings.log_level.value,
        json_format=state.settings.logging.json_format,
    )
    app.state.settings = state.settings
    app.state.logger = state.logger
    state.logger.info("starting api")
    yield
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
