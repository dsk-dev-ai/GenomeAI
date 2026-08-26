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
    DuplicateDatasetError,
    DuplicateDataSourceError,
    DuplicateExperimentError,
    DuplicateExternalIdentifierError,
    DuplicateGeneError,
    DuplicateGenomeAccessionError,
    DuplicateProjectError,
    DuplicateProteinError,
    DuplicateSampleError,
    DuplicateStudyError,
    DuplicateTranscriptError,
    DuplicateVariantError,
    InvalidForeignKeyError,
)
from genomeai_api.integration.errors import (
    ConnectorNotFoundError,
    DataSourceNotFoundError,
    IntegrationConfigurationError,
    InvalidJobTransitionError,
    UnsafeSourceUrlError,
)
from genomeai_api.ratelimit import LimitController, RateLimitMiddleware
from genomeai_api.ratelimit.config import RateLimitConfig
from genomeai_api.ratelimit.limiter import RateLimiter
from genomeai_api.routes.admin_limits import router as admin_limits_router
from genomeai_api.routes.datasets import router as datasets_router
from genomeai_api.routes.experiments import router as experiments_router
from genomeai_api.routes.genes import router as genes_router
from genomeai_api.routes.genes_enhanced import router as genes_enhanced_router
from genomeai_api.routes.genomes import router as genomes_router
from genomeai_api.routes.health import router as health_router
from genomeai_api.routes.integrations import router as integrations_router
from genomeai_api.routes.projects import router as projects_router
from genomeai_api.routes.proteins import router as proteins_router
from genomeai_api.routes.samples import router as samples_router
from genomeai_api.routes.schedules import router as schedules_router
from genomeai_api.routes.search import router as search_router
from genomeai_api.routes.studies import router as studies_router
from genomeai_api.routes.transcripts import router as transcripts_router
from genomeai_api.routes.variants import router as variants_router
from genomeai_api.routes.workflows import router as workflows_router
from genomeai_api.state import AppState
from genomeai_api.workflows.errors import (
    ScheduleNotFoundError,
    ScheduleStateTransitionError,
    ScheduleValidationError,
    WorkflowNotFoundError,
    WorkflowRunNotFoundError,
    WorkflowStateTransitionError,
    WorkflowValidationError,
)


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

    rate_config = RateLimitConfig.from_env()
    rate_limiter = RateLimiter(state.redis, key_prefix="genomeai:rl")
    controller = LimitController(rate_limiter, rate_config)
    state.limit_controller = controller
    state.logger.info(
        "rate limiter initialized (enabled=%s, rpm=%d, rph=%d)",
        rate_config.enabled,
        rate_config.global_requests_per_minute,
        rate_config.global_requests_per_hour,
    )

    yield

    await shutdown_cache(state)
    await shutdown_db(state)
    state.logger.info("stopping api")


app = FastAPI(
    title="GenomeAI API",
    version="0.1.0",
    lifespan=lifespan,
)

_rate_config = RateLimitConfig.from_env()
if _rate_config.enabled:
    _rate_limiter = RateLimiter(None, key_prefix="genomeai:rl")
    app.add_middleware(RateLimitMiddleware, limiter=_rate_limiter, config=_rate_config)

app.include_router(datasets_router)
app.include_router(experiments_router)
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(search_router)
app.include_router(studies_router)
app.include_router(genomes_router)
app.include_router(samples_router)
app.include_router(genes_router)
app.include_router(genes_enhanced_router)
app.include_router(variants_router)
app.include_router(transcripts_router)
app.include_router(proteins_router)
# Schedules router first: its static /workflows/schedules* paths must win
# over the workflows router's dynamic /{workflow_id} routes.
app.include_router(schedules_router)
app.include_router(workflows_router)
if load_settings().integration.enable_integration_routes:
    app.include_router(integrations_router)
app.include_router(admin_limits_router)


@app.exception_handler(DuplicateGenomeAccessionError)
async def duplicate_genome_accession_handler(
    request: Request,
    exc: DuplicateGenomeAccessionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateProjectError)
async def duplicate_project_handler(
    request: Request,
    exc: DuplicateProjectError,
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


@app.exception_handler(DuplicateDatasetError)
async def duplicate_dataset_handler(
    request: Request,
    exc: DuplicateDatasetError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateStudyError)
async def duplicate_study_handler(
    request: Request,
    exc: DuplicateStudyError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateExperimentError)
async def duplicate_experiment_handler(
    request: Request,
    exc: DuplicateExperimentError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidForeignKeyError)
async def invalid_foreign_key_handler(
    request: Request,
    exc: InvalidForeignKeyError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
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


@app.exception_handler(DuplicateDataSourceError)
async def duplicate_data_source_handler(
    request: Request,
    exc: DuplicateDataSourceError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DuplicateExternalIdentifierError)
async def duplicate_external_identifier_handler(
    request: Request,
    exc: DuplicateExternalIdentifierError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(DataSourceNotFoundError)
async def data_source_not_found_handler(
    request: Request,
    exc: DataSourceNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConnectorNotFoundError)
async def connector_not_found_handler(
    request: Request,
    exc: ConnectorNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(UnsafeSourceUrlError)
async def unsafe_source_url_handler(
    request: Request,
    exc: UnsafeSourceUrlError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(IntegrationConfigurationError)
async def integration_configuration_handler(
    request: Request,
    exc: IntegrationConfigurationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidJobTransitionError)
async def invalid_job_transition_handler(
    request: Request,
    exc: InvalidJobTransitionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(WorkflowValidationError)
async def workflow_validation_handler(
    request: Request,
    exc: WorkflowValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": str(exc), "issues": exc.issues},
    )


@app.exception_handler(WorkflowNotFoundError)
async def workflow_not_found_handler(
    request: Request,
    exc: WorkflowNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(WorkflowRunNotFoundError)
async def workflow_run_not_found_handler(
    request: Request,
    exc: WorkflowRunNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(WorkflowStateTransitionError)
async def workflow_state_transition_handler(
    request: Request,
    exc: WorkflowStateTransitionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(ScheduleNotFoundError)
async def schedule_not_found_handler(
    request: Request,
    exc: ScheduleNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(ScheduleValidationError)
async def schedule_validation_handler(
    request: Request,
    exc: ScheduleValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": str(exc), "issues": exc.issues},
    )


@app.exception_handler(ScheduleStateTransitionError)
async def schedule_state_transition_handler(
    request: Request,
    exc: ScheduleStateTransitionError,
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
