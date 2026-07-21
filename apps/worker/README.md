# `apps/worker` — Background Worker

Future home of the GenomeAI background job processor.

**Planned stack:** Python, Celery / Arq, Redis

This service will execute asynchronous tasks: pipeline steps, data ingestion, cleanup, and notifications.
