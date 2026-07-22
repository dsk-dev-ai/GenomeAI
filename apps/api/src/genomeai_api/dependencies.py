from __future__ import annotations

from fastapi import Request
from genomeai_config import Settings

from genomeai_api.state import AppState


def get_settings(request: Request) -> Settings:
    state: AppState = request.app.state
    return state.settings


def get_app_state(request: Request) -> AppState:
    state: AppState = request.app.state
    return state
