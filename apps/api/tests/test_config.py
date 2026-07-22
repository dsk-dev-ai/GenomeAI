from __future__ import annotations

import os
from unittest import mock

import pydantic
import pytest
from genomeai_config import (
    AppSettings,
    DatabaseSettings,
    Environment,
    LoggingSettings,
    LogLevel,
    RedisSettings,
    Settings,
    load_settings,
)


def test_settings_defaults() -> None:
    app = AppSettings()
    assert app.service_name == "genomeai"
    assert app.version == "0.1.0"
    assert app.debug is True
    assert app.environment == Environment.DEVELOPMENT
    db = DatabaseSettings()
    assert db.host == "localhost"
    assert db.port == 5432
    redis = RedisSettings()
    assert redis.host == "localhost"
    assert redis.port == 6379
    log = LoggingSettings()
    assert log.level == LogLevel.INFO
    assert log.json_format is False


def test_env_overrides() -> None:
    env = {
        "GENOMEAI_APP_SERVICE_NAME": "test-service",
        "GENOMEAI_APP_DEBUG": "false",
        "GENOMEAI_APP_ENVIRONMENT": "production",
        "GENOMEAI_DATABASE_HOST": "db.example.com",
        "GENOMEAI_DATABASE_PORT": "15432",
        "GENOMEAI_REDIS_HOST": "redis.example.com",
        "GENOMEAI_REDIS_PORT": "16379",
        "GENOMEAI_LOGGING_LEVEL": "DEBUG",
        "GENOMEAI_LOGGING_JSON_FORMAT": "true",
    }
    with mock.patch.dict(os.environ, env, clear=False):
        app = AppSettings()
        db = DatabaseSettings()
        redis = RedisSettings()
        log = LoggingSettings()
    assert app.service_name == "test-service"
    assert app.debug is False
    assert app.environment == Environment.PRODUCTION
    assert db.host == "db.example.com"
    assert db.port == 15432
    assert redis.host == "redis.example.com"
    assert redis.port == 16379
    assert log.level == LogLevel.DEBUG
    assert log.json_format is True


def test_database_url() -> None:
    from urllib.parse import quote

    db = DatabaseSettings()
    expected = f"postgresql+asyncpg://{quote(db.user)}:{quote(db.password)}@{db.host}:{db.port}/{quote(db.database)}"
    assert db.url == expected


def test_redis_url_no_password() -> None:
    redis = RedisSettings(password="")
    assert redis.url == f"redis://{redis.host}:{redis.port}/{redis.db}"


def test_redis_url_with_password() -> None:
    redis = RedisSettings(password="secret")
    assert redis.url == f"redis://:secret@{redis.host}:{redis.port}/{redis.db}"


def test_composite_settings() -> None:
    app = AppSettings()
    db = DatabaseSettings()
    redis = RedisSettings()
    log = LoggingSettings()
    settings = Settings(app=app, database=db, redis=redis, logging=log)
    assert settings.service_name == settings.app.service_name
    assert settings.log_level == settings.logging.level
    assert settings.debug == settings.app.debug
    assert settings.environment == settings.app.environment


def test_composite_immutable() -> None:
    app = AppSettings()
    db = DatabaseSettings()
    redis = RedisSettings()
    log = LoggingSettings()
    settings = Settings(app=app, database=db, redis=redis, logging=log)
    with pytest.raises(pydantic.ValidationError):
        settings.app.service_name = "changed"  # type: ignore[misc]


def test_database_min_size_zero_raises() -> None:
    with pytest.raises(pydantic.ValidationError):
        DatabaseSettings(min_size=0)


def test_database_max_size_zero_raises() -> None:
    with pytest.raises(pydantic.ValidationError):
        DatabaseSettings(max_size=0)


def test_load_settings_returns_composite() -> None:
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert isinstance(settings.app, AppSettings)
    assert isinstance(settings.database, DatabaseSettings)
    assert isinstance(settings.redis, RedisSettings)
    assert isinstance(settings.logging, LoggingSettings)
