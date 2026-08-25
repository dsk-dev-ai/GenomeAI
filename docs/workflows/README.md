# Workflow Foundation (7.1) · Execution (7.2) · Scheduler (7.3)

The Workflow Foundation establishes GenomeAI's workflow/DAG architecture:
workflow definitions, ordered and connected steps, deterministic DAG
validation, execution-state models, persistence, and a minimal admin API.
Phase 7.2 adds deterministic, sequential, **in-process** execution on top;
Phase 7.3 adds application-level **scheduling** that decides WHEN runs
start.

> Execution is synchronous: one API call drives one run step by step to a
> terminal state. Scheduling is application-level: due-run detection only
> advances when `/workflows/schedules/evaluate` is called. There is still
> no queue, worker, background daemon, or parallel execution engine —
> those belong to later milestones.

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

## What does NOT exist yet

- No background execution, daemon, timer loop, or workers — evaluation
  happens only when the evaluate endpoint (or a test) calls it
- No Redis/Celery/Arq queues, no parallel engine, no retries
- No artifact storage, caching beyond step outputs, or real executors —
  step execution is still a deterministic passthrough placeholder
