from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENOMEAI_APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    service_name: str = "genomeai"
    version: str = "0.1.0"
    debug: bool = True
    environment: Environment = Environment.DEVELOPMENT


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENOMEAI_DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "genomeai"
    password: str = ""
    database: str = "genomeai"
    min_size: int = Field(default=5, ge=1)
    max_size: int = Field(default=20, ge=1)

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENOMEAI_REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENOMEAI_LOGGING_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    level: LogLevel = LogLevel.INFO
    json_format: bool = False


@dataclass(frozen=True)
class Settings:
    app: AppSettings
    database: DatabaseSettings
    redis: RedisSettings
    logging: LoggingSettings

    @property
    def service_name(self) -> str:
        return self.app.service_name

    @property
    def log_level(self) -> LogLevel:
        return self.logging.level

    @property
    def debug(self) -> bool:
        return self.app.debug

    @property
    def environment(self) -> Environment:
        return self.app.environment


@lru_cache
def load_settings() -> Settings:
    return Settings(
        app=AppSettings(),
        database=DatabaseSettings(),
        redis=RedisSettings(),
        logging=LoggingSettings(),
    )
