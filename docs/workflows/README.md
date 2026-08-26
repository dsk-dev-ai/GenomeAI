# Workflow Foundation (7.1) · Execution (7.2) · Scheduler (7.3) · Queue & Worker (7.4) · Retry & Failure (7.5)

The Workflow Foundation establishes GenomeAI's workflow/DAG architecture:
workflow definitions, ordered and connected steps, deterministic DAG
validation, execution-state models, persistence, and a minimal admin API.
Phase 7.2 adds deterministic, sequential, **in-process** execution on top;
Phase 7.3 adds application-level **scheduling** that decides WHEN runs
start; Phase 7.4 adds a **queue and worker** so runs can execute in the
background; Phase 7.5 adds a **retry and failure-handling** layer.

> Direct execution remains synchronous: one API call drives one run step
> by step to a terminal state. Scheduling is application-level: due-run
> detection advances when `/workflows/schedules/evaluate` is called.
> Phase 7.4 adds optional background execution: pending runs can be
> enqueued (`POST /workflows/runs/{id}/queue` or via the scheduler) and a
> worker process claims them and drives the same DAG engine. Phase 7.5
> adds automatic retry with configurable failure classification, backoff,
> and attempt tracking — plus a manual retry endpoint. Still absent:
> parallel step execution, autoscaling, Kubernetes/HPC — those
> belong to later milestones. See [queue-worker.md](queue-worker.md)
> and [retry-failure.md](retry-failure.md).

## Core concepts

| Concept | Table | Purpose |
| --- | --- | --- |
| `Workflow` | `workflows` | A reusable workflow *definition* (name, version, status) |
| `WorkflowStep` | `workflow_steps` | One logical, typed step inside a definition |
| `WorkflowDependency` | `workflow_dependencies` | A directed edge `step A → step B` within one definition |
| `WorkflowRun` | `workflow_runs` | One requested execution of a workflow definition |
| `StepRun` | `workflow_step_runs` | Execution state of one step within one run |

A **definition** describes *what could run*; a **run** records *that an
execution was requested*. Phase 7.1 implements definitions fully and runs
only as state containers.

## What exists in 7.1

- Workflow/step/dependency CRUD via the service and repository layers
- Deterministic DAG validation (cycles, self-dependencies, missing steps,
  duplicates) before anything is persisted — see [dag.md](dag.md)
- Typed execution states (`pending`, `running`, `succeeded`, `failed`,
  `cancelled`) with an explicit transition table
- Run creation that initializes one `StepRun` per step in deterministic
  topological order
- Minimal REST API under `/workflows`

## What exists in 7.2

- `DAGExecutionEngine`: sequential in-process execution of one run,
  dependency-aware ready-step scheduling in persisted position order
- Pluggable `StepExecutor` abstraction with a deterministic passthrough
  default (`fail_with_message` trigger for failure tests)
- Failure propagation: failing step → dependents cancelled, run failed,
  reason preserved on both step and run; no retries
- Cancellation checks before and during execution; completed steps are
  preserved
- Per-step result capture (`output`) and error reasons (`error_message`)
- `POST /workflows/runs/{run_id}/execute` (synchronous)

See [execution.md](execution.md) for the full contract.

## What exists in 7.3

- `SchedulerService`: deterministic due-run detection over enabled
  schedules, creating pending runs through the existing repository path
- One-time (`run_at`) and recurring (standard cron via an isolated
  `OccurrenceCalculator` abstraction) schedules with per-schedule IANA
  timezone
- Lifecycle `enabled ⇄ disabled`, one-time → `completed` after firing,
  with illegal moves rejected (409)
- DB-enforced idempotency: `(schedule_id, scheduled_for)` annotation on
  `workflow_runs` plus a partial unique index — repeated evaluations
  never duplicate an occurrence
- Injected `Clock`/calculator so core logic is fully deterministic and
  testable; timezone-aware timestamps everywhere (DST verified)
- Minimal schedule API including one synchronous
  `POST /workflows/schedules/evaluate` pass

See [scheduler.md](scheduler.md) for the full contract.

## What exists in 7.4

- `JobQueue` protocol with two implementations: `InMemoryJobQueue`
  (reference/tests) and `RedisJobQueue` (the only Redis-aware module)
- Deterministic job codec (`WorkflowJob` ↔ sorted compact JSON, UTC
  timestamps, schema version field); malformed payloads raise typed errors
- Exclusive claims via atomic list moves, idempotent enqueue per run,
  guarded release; connection failures surface as `QueueUnavailableError`
- `WorkflowRunWorker`: claim → verify run is still pending → delegate to
  the existing DAG engine → release. Cancelled/completed runs are never
  re-executed; failures mark both run and job without losing messages
- Graceful shutdown (`run_forever(stop_event)`), standalone
  `genomeai-worker` console script (SIGINT/SIGTERM safe)
- API: `POST /workflows/runs/{run_id}/queue` → 202 (404/409/503 mapped);
  direct `/execute` retained for tests/internal use
- Scheduler enqueues every run it creates when a queue is configured;
  schedule bookkeeping always happens first

See [queue-worker.md](queue-worker.md) for the full contract.

## What exists in 7.5

- `RetryPolicy` frozen dataclass with `max_attempts`, `retryable` set,
  and pluggable `Backoff` — the Worker asks this, never decides on its own
- Five-class deterministic failure classification (`transient`, `permanent`,
  `cancellation`, `invalid_workflow`, `infrastructure`) via `classify_failure`
- `FixedBackoff` and `ExponentialBackoff` (deterministic, capped, no jitter)
- Attempt tracking columns on `workflow_runs`: `attempt_count`,
  `failure_class`, `next_retry_at`, `failure_history` (append-only JSONB)
- Atomic `JobQueue.reschedule(job, delay)` — crash-safe release + requeue
  in one step; delayed jobs promoted via ZSET/h heapq
- Worker pre-flight: FAILED+due → reopen + re-execute; premature delivery
  → reschedule without executing
- `POST /workflows/runs/{run_id}/retry` manual retry (202/404/409/503)
- Final failure: run stays FAILED with full history; no physical dead-letter

See [retry-failure.md](retry-failure.md) for the full contract.

## What does NOT exist yet

- No per-step retry (workflow-level only in this phase)
- No parallel step execution, priority queues, visibility timeouts, or
  workflow caching
- No multiple-worker orchestration, autoscaling, Kubernetes/HPC targets —
  one worker process per deployment is the supported shape
- No artifact storage or real executors — step execution is still a
  deterministic passthrough placeholder
