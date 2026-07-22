from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from genomeai_config import load_settings
from genomeai_logging import configure_logging, get_logger

from genomeai_api.cache import create_redis, shutdown_redis, verify_redis
from genomeai_api.database import create_engine, create_session_factory, dispose_engine
from genomeai_api.exceptions import (
    DuplicateGeneError,
    DuplicateGenomeAccessionError,
    DuplicateProteinError,
    DuplicateSampleError,
    DuplicateTranscriptError,
    DuplicateVariantError,
)
from genomeai_api.routes.genes import router as genes_router
from genomeai_api.routes.genomes import router as genomes_router
from genomeai_api.routes.health import router as health_router
from genomeai_api.routes.proteins import router as proteins_router
from genomeai_api.routes.samples import router as samples_router
from genomeai_api.routes.transcripts import router as transcripts_router
from genomeai_api.routes.variants import router as variants_router
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
app.include_router(genomes_router)
app.include_router(samples_router)
app.include_router(genes_router)
app.include_router(variants_router)
app.include_router(transcripts_router)
app.include_router(proteins_router)


@app.exception_handler(DuplicateGenomeAccessionError)
async def duplicate_genome_accession_handler(
    request: Request,
    exc: DuplicateGenomeAccessionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateSampleError)
async def duplicate_sample_handler(
    request: Request,
    exc: DuplicateSampleError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateGeneError)
async def duplicate_gene_handler(
    request: Request,
    exc: DuplicateGeneError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateVariantError)
async def duplicate_variant_handler(
    request: Request,
    exc: DuplicateVariantError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateTranscriptError)
async def duplicate_transcript_handler(
    request: Request,
    exc: DuplicateTranscriptError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateProteinError)
async def duplicate_protein_handler(
    request: Request,
    exc: DuplicateProteinError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


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
