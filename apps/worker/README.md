# `apps/worker` — Background Worker

Asynchronous background job processor.

**Technology:** Python 3.12+, asyncio
**Entry point:** `src/genomeai_worker/main.py` — `main()`
**Capabilities:**
- Graceful shutdown on SIGTERM/SIGINT
- Structured logging
- Pluggable job processing

**Future responsibilities:** Pipeline execution, data ingestion, cleanup tasks.
