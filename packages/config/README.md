# `packages/config` — Configuration Library

Centralized application configuration with environment variable loading and validation.

Provides `genomeai-config` Python package with:
- `Settings` — Pydantic-based settings with `.env` support
- `Environment` — Enum for dev/staging/prod
- `LogLevel` — Enum for log levels
- `load_settings()` — Cached settings factory
