# `packages/shared` — Shared Utilities

Shared exceptions, constants, and base models used across GenomeAI Python services.

Provides `genomeai-shared` Python package with:
- `GenomeAIError` / `ConfigurationError` / `ValidationError` / `ApplicationError` — Exception hierarchy
- `APP_NAME` / `VERSION` — Application constants
- `BaseModel` — Dataclass base with `to_dict()` and `from_dict()`
