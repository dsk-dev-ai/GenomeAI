from __future__ import annotations

from typing import cast

from fastapi import Request
from genomeai_config import Settings

from genomeai_api.state import AppState


def get_settings(request: Request) -> Settings:
    state = cast(AppState, request.app.state.app_state)
    return state.settings


def get_app_state(request: Request) -> AppState:
    return cast(AppState, request.app.state.app_state)
