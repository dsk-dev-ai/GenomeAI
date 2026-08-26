# Workflow Queue & Worker (Phase 7.4)

Phase 7.4 adds GenomeAI's **first background execution layer** on top of
the Phase 7.1 foundation, Phase 7.2 engine, and Phase 7.3 scheduler.

Phase 7.3 decides WHEN a workflow should run. Phase 7.4 provides the
infrastructure that lets a `WorkflowRun` be QUEUED and processed later by
a WORKER, which drives the existing `DAGExecutionEngine`. Scheduling,
queueing, and execution remain three separate responsibilities.

> **Scope guard.** This phase introduces a single-process worker with an
> in-app queue abstraction and a Redis backend. Phase 7.5 adds retry
> and failure handling on top (see [retry-failure.md](retry-failure.md)).
> Still absent: priority scheduling, parallel DAG execution, workflow
> caching, autoscaling, Kubernetes/HPC deployment, and distributed
> coordination.

## Architecture

```
SchedulerService (7.3)                POST /workflows/runs/{id}/queue
  evaluate_due()                       POST /workflows/runs/{id}/retry
    → creates pending WorkflowRun     WorkflowService.queue_run / retry_run
    → queue.enqueue(run.id)             (idempotent, never executes)
         ↓
      JobQueue  ← workflows/queueing.py (protocol + in-memory reference)
                  workflows/redis_queue.py (Redis backend, isolated)
      + reschedule(job, delay)  (Phase 7.5: atomic release + requeue)
      + delayed()               (Phase 7.5: scheduled-jobs count)
         ↓
      WorkflowRunWorker   services/worker.py
        claim → verify state → [re-open if retry due] → engine.execute_run()
        failure → classify → RetryPolicy.decide → reschedule or final-fail
         ↓
      DAGExecutionEngine (unchanged 7.2)  → StepRuns advance as before
```

Responsibility boundaries:

| Component | Owns | Never does |
| --- | --- | --- |
| `SchedulerService` | due detection, run creation, enqueue | executing steps |
| `WorkflowService.queue_run / retry_run` | queued-run lifecycle at the API boundary | planning, executing |
| `JobQueue` implementations | durable job transport, claim exclusivity, atomic reschedule | interpreting runs |
| `WorkflowRunWorker` | decide WHETHER a claimed run may execute (policy-injected), failure classification + requeue | DAG planning, retry policy decisions |
| `RetryPolicy` (Phase 7.5) | budget, retryable classes, backoff delay | Worker logic, queue operations |
| `DAGExecutionEngine` | driving a pending run to a terminal state | queueing, scheduling |

## Queue technology

Redis was chosen because it is already part of the stack (`cache/redis.py`,
`AppState.redis`, health checks, dev container on port 6380) — no new
dependency, no Celery/Arq, no broker deployment. Two hard rules:

1. **Isolation.** Exactly one module touches Redis:
   `workflows/redis_queue.py`. Everything else depends only on the
   `JobQueue` protocol from `workflows/queueing.py`, so the backend is
   replaceable (an `InMemoryJobQueue` ships as the reference/test double).
2. **Deterministic serialization.** Jobs are encoded by
   `job_to_json` / `job_from_json`: frozen dataclass, sorted keys,
   compact separators, UTC ISO-8601 timestamps (naive datetimes are
   rejected), explicit `schema: 1` version field. Byte-identical payloads
   make exact-list-removal and idempotency guards reliable.

Connection failures never leak raw exceptions into domain code: every
backend call is wrapped so callers see `QueueUnavailableError`
(`workflow.queue-unavailable`); undecodable payloads raise
`JobDecodeError` (`workflow.job-decode-error`).

## Job model

`WorkflowJob` identifies a run; it deliberately does NOT duplicate the
run's domain state:

| Field | Meaning |
| --- | --- |
| `job_id` | queue identity of this message |
| `workflow_run_id` | the ONE source of truth for execution state: the existing `WorkflowRun` row |
| `queued_at` / `claimed_at` / `completed_at` | lifecycle timestamps (UTC) |
| `attempt` | reserved for future retry handling (always 1 today) |
| `state` | queued / running / completed / failed (`JobState`) |

The `WorkflowRun` stays the authority for whether work happens; the job
is only a pointer plus bookkeeping. No new database table exists — Redis
is the queue source of truth, so there is no duplicate job store to keep
consistent.

## Job & WorkflowRun lifecycles

Two small state machines cooperate:

```
JobState:      queued → running → completed
                             → failed

RunState:      pending → running → succeeded / failed
                 → cancelled            (pre-execution cancellation)
```

Rules that tie them together:

- A run may be enqueued only while `pending`; anything else answers
  `409 Conflict` (`WorkflowStateTransitionError(current, "queued")`).
- Cancellation compatibility: if a run is cancelled after its job was
  enqueued, the worker loads the run, sees a non-pending state, marks the
  job completed, and SKIPS execution. A queued cancelled run is never
  executed.
- The worker marks a run `failed` only when the engine raises; it never
  reports success unless `engine.execute_run()` returned.

## Claiming & idempotency

The Redis layout under prefix `genomeai:workflow-runs`:

| Key | Type | Purpose |
| --- | --- | --- |
| `:queued` | LIST | waiting payloads (right-push) |
| `:processing` | LIST | claimed payloads (left-move target) |
| `:active` | HASH run_id → queued payload | enqueue guard: `HSETNX` makes repeated enqueues idempotent per run |
| `:claims` | HASH job_id → claimed payload | remembers exactly WHAT bytes were claimed so release can remove them precisely |

- **Claim** is one atomic `LMOVE queued→processing (RIGHT, LEFT)` — two
  workers can never receive the same payload.
- **Enqueue** writes the `:active` guard first; a loser reads the winner's
  payload and returns THAT job id instead of pushing a second message.
  Duplicate queue messages therefore collapse to one delivery.
- **Release** (complete or fail) is a transactional pipeline: remove the
  exact claimed bytes from `:processing`, delete the claim hash entry,
  delete the `:active` guard so the run can be queued again later.
- **Already-completed/cancelled runs**: even if a stale message arrives,
  the worker's pre-flight check retires it without touching the engine.
- A crash between claim and release leaves the payload on
  `:processing` where recovery tooling can find it; automated recovery is
  deferred (see below).

## Worker architecture

`WorkflowRunWorker` contains no DAG logic. Per cycle:

1. `claim(worker_id)` — no job → idle sleep.
2. Load the run through a FRESH session (`store_factory` context manager;
   sessions are never shared across jobs).
3. Pre-flight: missing run → `fail(job)` (never silently lost);
   non-pending → `complete(job)` + skip.
4. Build the engine via `engine_factory(store)` and call `execute_run()`
   once. A `WorkflowStateTransitionError` means another executor won the
   race — the message is retired without duplicate execution.
5. Success → `complete(job)`; unexpected exception → best-effort
   `transition_run(FAILED, "worker execution error: …")` then
   `fail(job, reason)`.

Every outcome is classified as one of: `no_job`, `executed`,
`skipped_state`, `skipped_race`, `missing_run`, `execution_failed`,
`worker_error`.

## Graceful shutdown

`worker.run_forever(stop_event)`:

- Stops CLAIMING immediately when `stop_event` is set (checked each loop).
- An in-flight job finishes first; shutdown never abandons a claimed job.
- Idle waits use `asyncio.wait_for(stop.wait(), timeout=poll_interval)`
  so SIGTERM wakes the loop at once instead of after the poll interval.
- On exit the queue is closed (`finally`) and resources released; the
  standalone process (`genomeai-worker` console script,
  `apps/api/src/genomeai_api/worker.py`) traps SIGINT/SIGTERM into the
  stop event, then disposes the Redis pool and SQLAlchemy engine.

## Scheduler integration

`SchedulerService` accepts an optional `JobQueue`. During
`evaluate_due()`, for each run it actually creates (duplicates are still
suppressed first), it calls `queue.enqueue(run.id)` AFTER recording the
occurrence — bookkeeping-first ordering means a queue outage can never
strand schedule state, and the scheduler never executes anything. With no
queue configured the scheduler behaves exactly as in Phase 7.3.

## API integration

- `POST /workflows/runs/{run_id}/queue` → **202 Accepted** with the job
  identity and current run snapshot. The request does NOT execute the DAG
  and does not block on it. Idempotent repeats return the original job id.
- Errors: unknown run → 404; illegal transition → 409; unconfigured/
  unreachable queue → **503** (`QueueUnavailableError`).
- `POST /workflows/runs/{run_id}/execute` remains available unchanged for
  tests/internal use (Phase 7.2 synchronous path).

## Failure behavior summary

| Situation | Outcome |
| --- | --- |
| Queue unreachable (API side) | 503, nothing enqueued, schedule state intact |
| Run deleted before pickup | job failed with reason, never lost silently |
| Cancelled/completed run picked up | job completed, engine untouched |
| Engine race (two executors) | loser retires message, DB truth prevails |
| Engine exception | run marked failed with message, job failed with reason |
| Worker crash mid-job | payload remains on processing list (recovery deferred) |
| Unexpected worker error | job released with reason; worker survives and continues |

## What exists in 7.4 vs. what is deferred

Exists now: queue protocol + two backends, deterministic job codec,
exclusive claims, idempotent enqueue, guarded release, single worker loop
with graceful shutdown, scheduler/API integration, `genomeai-worker`
process, full test coverage.

Deferred to Phase 7.5+ (by design): retries/backoff, dead-letter queues,
crash-recovery scanning of the processing list, multiple workers /
competing consumers beyond LMOVE exclusivity, parallel step execution,
priority queues, visibility timeouts, workflow caching, autoscaling,
Kubernetes/HPC orchestration, distributed multi-region execution.
