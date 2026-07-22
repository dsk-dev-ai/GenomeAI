# `apps/api` — REST API

FastAPI application exposing health endpoints.

**Technology:** FastAPI, Uvicorn, Python 3.12+
**Entry point:** `src/genomeai_api/main.py` — `main()`
**Endpoints:**
- `GET /` — Root health check
- `GET /health` — Health check
- `GET /ready` — Readiness check
- `GET /live` — Liveness check

**Future responsibilities:** Pipeline management, data queries, analysis orchestration.
