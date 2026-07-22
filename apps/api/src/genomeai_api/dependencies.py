from __future__ import annotations

from typing import cast

from fastapi import Request
from genomeai_config import Settings
from redis.asyncio import Redis

from genomeai_api.database.session import get_db_session
from genomeai_api.state import AppState


def get_settings(request: Request) -> Settings:
    state = cast(AppState, request.app.state.app_state)
    return state.settings


def get_app_state(request: Request) -> AppState:
    return cast(AppState, request.app.state.app_state)


def get_redis(request: Request) -> Redis:
    state = cast(AppState, request.app.state.app_state)
    if state.redis is None:
        raise RuntimeError("redis not initialized")
    return state.redis


__all__ = [
    "get_app_state",
    "get_db_session",
    "get_redis",
    "get_settings",
]
