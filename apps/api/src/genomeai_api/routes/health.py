from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from genomeai_api.state import AppState

router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> dict[str, str]:
    state = cast(AppState, request.app.state.app_state)
    checks: dict[str, str] = {"status": "ok"}
    if state.db_engine is not None:
        try:
            async with state.db_engine.connect() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"
            checks["status"] = "degraded"
    else:
        checks["database"] = "not_configured"
    if state.redis is not None:
        try:
            ok = await state.redis.ping()
            checks["redis"] = "ok" if ok else "error"
        except Exception:
            checks["redis"] = "error"
            checks["status"] = "degraded"
    else:
        checks["redis"] = "not_configured"
    return checks


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}
