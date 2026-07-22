from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from genomeai_config import load_settings
from genomeai_logging import get_logger, setup_logging

from genomeai_api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = load_settings()
    setup_logging(level=settings.log_level.value, name=settings.service_name)
    logger = get_logger(settings.service_name)
    logger.info("starting api")
    yield
    logger.info("stopping api")


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
