from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient
from genomeai_api.dependencies import get_app_state, get_settings
from genomeai_api.state import AppState
from genomeai_config import AppSettings, DatabaseSettings, LoggingSettings, RedisSettings, Settings
from genomeai_logging import configure_logging


def _test_settings() -> Settings:
    return Settings(
        app=AppSettings(
            service_name="test-service",
            debug=False,
            environment="development",
            version="0.1.0",
        ),
        database=DatabaseSettings(
            host="db.example.com",
            port=15432,
            user="test",
            password="secret",
            database="testdb",
            min_size=2,
            max_size=10,
        ),
        redis=RedisSettings(host="redis.example.com", port=16379, db=1, password="rsecret"),
        logging=LoggingSettings(level="DEBUG", json_format=True),
    )


def test_get_settings_dependency() -> None:
    app = FastAPI()
    settings = _test_settings()
    configure_logging()
    app.state.settings = settings
    app.state.logger = logging.getLogger("genomeai.api.test")

    @app.get("/check")
    async def check(settings: Settings = Depends(get_settings)) -> dict[str, str]:
        return {"service": settings.app.service_name}

    with TestClient(app) as client:
        resp = client.get("/check")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"service": "test-service"}


def test_app_state_dependency() -> None:
    app = FastAPI()
    settings = _test_settings()
    state = AppState(settings=settings, logger=logging.getLogger("genomeai.api.test"))
    app.state = state

    @app.get("/state")
    async def check(state: AppState = Depends(get_app_state)) -> dict[str, str]:
        return {"service": state.settings.app.service_name}

    with TestClient(app) as client:
        resp = client.get("/state")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"service": "test-service"}
