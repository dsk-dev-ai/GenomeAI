from __future__ import annotations

import secrets
from typing import cast

from fastapi import Header, HTTPException, Request, status
from genomeai_config import Settings

from genomeai_api.database.session import get_db_session
from genomeai_api.state import AppState


def get_settings(request: Request) -> Settings:
    state = cast(AppState, request.app.state.app_state)
    return state.settings


def get_app_state(request: Request) -> AppState:
    return cast(AppState, request.app.state.app_state)


def require_admin_token(
    request: Request,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """Fail-closed shared-secret guard for admin and internal integration routes.

    The token is configured via GENOMEAI_APP_ADMIN_TOKEN. When it is unset the
    routes are effectively disabled (503), so a misconfiguration cannot expose
    mutating admin endpoints. Comparison uses a constant-time helper.
    """
    expected = get_settings(request).app.admin_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin token is not configured; admin routes are disabled",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )


__all__ = [
    "get_app_state",
    "get_db_session",
    "get_settings",
    "require_admin_token",
]
