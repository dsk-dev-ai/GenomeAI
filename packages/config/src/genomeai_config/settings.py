from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from urllib.parse import quote

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
    workflow_max_concurrency: int = Field(default=1, ge=1)


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
        return f"postgresql+asyncpg://{quote(self.user)}:{quote(self.password)}@{self.host}:{self.port}/{quote(self.database)}"


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


class IntegrationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENOMEAI_INTEGRATION_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    # HTTP(S) origin allowlist for external source endpoints. Fail-closed:
    # when empty, the fetcher refuses to connect to anything. Each entry is a
    # base URL prefix a source's api_base_url must start with. This is the
    # primary SSRF control for the Data Integration Foundation.
    allowed_source_urls: list[str] = []

    # Default per-request timeout for external source fetches (seconds).
    request_timeout_seconds: float = 30.0

    # Default maximum automatic retry attempts per external fetch (0 disables
    # automatic retries). Individual connectors may override this.
    default_max_retries: int = 0

    # Feature flag controlling whether the internal integration admin routes
    # are mounted on the API.
    enable_integration_routes: bool = True


class RateLimitSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENOMEAI_RATELIMIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    enabled: bool = True

    global_requests_per_minute: int = Field(default=60, ge=0)
    global_requests_per_hour: int = Field(default=1000, ge=0)
    global_requests_per_day: int = Field(default=10000, ge=0)

    per_endpoint_requests_per_minute: int = Field(default=30, ge=0)
    per_endpoint_requests_per_hour: int = Field(default=500, ge=0)

    burst_size: int = Field(default=10, ge=0)
    burst_window_seconds: int = Field(default=1, ge=1)

    ai_tokens_per_minute: int = Field(default=100_000, ge=0)
    ai_tokens_per_hour: int = Field(default=1_000_000, ge=0)
    ai_tokens_per_day: int = Field(default=5_000_000, ge=0)

    ai_requests_per_minute: int = Field(default=20, ge=0)
    ai_requests_per_hour: int = Field(default=500, ge=0)
    ai_requests_per_day: int = Field(default=3000, ge=0)

    ollama_enabled: bool = True
    ollama_requests_per_minute: int = Field(default=999_999, ge=0)
    ollama_requests_per_day: int = Field(default=999_999, ge=0)

    gemini_enabled: bool = True
    gemini_requests_per_minute: int = Field(default=10, ge=0)
    gemini_requests_per_day: int = Field(default=250, ge=0)

    openrouter_enabled: bool = True
    openrouter_requests_per_minute: int = Field(default=20, ge=0)
    openrouter_requests_per_day: int = Field(default=50, ge=0)

    groq_enabled: bool = True
    groq_requests_per_minute: int = Field(default=30, ge=0)
    groq_requests_per_day: int = Field(default=1000, ge=0)

    mistral_enabled: bool = True
    mistral_requests_per_minute: int = Field(default=20, ge=0)
    mistral_requests_per_day: int = Field(default=33_000, ge=0)


@dataclass(frozen=True)
class Settings:
    app: AppSettings
    database: DatabaseSettings
    redis: RedisSettings
    logging: LoggingSettings
    integration: IntegrationSettings = field(default_factory=IntegrationSettings)
    ratelimit: RateLimitSettings = field(default_factory=RateLimitSettings)

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
        integration=IntegrationSettings(),
        ratelimit=RateLimitSettings(),
    )
