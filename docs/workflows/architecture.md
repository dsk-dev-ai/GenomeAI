# Workflow Architecture

```
API (FastAPI, /workflows)
 ↓
WorkflowService          ← DAG validation, run initialization (no execution)
 │                          queue_run(): enqueue a pending run (Phase 7.4)
 ↓
SchedulerService         ← due detection, scheduled run creation + enqueue (7.3/7.4)
 ├── planner / executor  ← pure occurrence math; one-step work abstraction
 ↓
JobQueue                 ← queue protocol; Redis backend isolated in one module (Phase 7.4)
 ↓
WorkflowRunWorker        ← claim → verify pending → delegate to engine (Phase 7.4)
 ↓
DAGExecutionEngine       ← sequential in-process execution (Phase 7.2)
 ↓
WorkflowRepository       ← persistence only
 ↓
SQLAlchemy models        ← workflows / workflow_steps / workflow_dependencies /
                            workflow_runs / workflow_step_runs / workflow_schedules
 ↓
PostgreSQL
```

## Layers

- **Routes** (`routes/workflows.py`): thin HTTP surface. Pydantic schemas in,
  response schemas out. Typed domain errors are mapped centrally in
  `main.py` (`WorkflowValidationError` → 422 with an `issues` list;
  not-found errors → 404; illegal state transitions → 409).
- **Service** (`services/workflow.py`): owns definition validation and run
  initialization. It validates the submitted graph **before** persisting and
  computes a deterministic topological order when a run is requested.
  The service never executes steps — execution lives in the engine layer.
- **Scheduler** (`services/scheduler.py`): answers "which enabled schedules
  are due to create WorkflowRuns?" via an injected `Clock` and pure
  occurrence calculator, creates pending runs through the same repository
  path as manual runs, and manages schedule lifecycle. It never executes
  steps and never reads the wall clock directly.
  See [scheduler.md](scheduler.md).
- **Queue & Worker** (Phase 7.4): `workflows/queueing.py` defines the
  `JobQueue` protocol and deterministic job codec;
  `workflows/redis_queue.py` is the only Redis-aware module;
  `services/worker.py` claims queued runs and delegates eligible ones to
  the engine. The API can queue a run (`202 Accepted`) without executing
  it; the scheduler enqueues what it creates. No retry, parallelism, or
  orchestration logic exists anywhere in this layer.
  See [queue-worker.md](queue-worker.md).
- **Engine** (`workflows/execution/engine.py`): drives one pending run to a
  terminal state, sequentially, in persisted position order. It owns every
  state transition, delegates ready-step selection to the pure planner,
  delegates step work to an injected `StepExecutor`, and persists only via
  the repository. See [execution.md](execution.md).
- **Repository** (`repositories/workflow.py`): persistence only. Creates
  workflows with eagerly generated step ids so dependency edges can be
  resolved by name before the flush; creates runs plus one pending
  `StepRun` per step; exposes intent-revealing transitions for runs and
  step runs (timestamp and result handling included).
- **Domain** (`workflows/dag.py`, `workflows/types.py`, `workflows/errors.py`):
  pure functions and typed vocabulary. No I/O, fully deterministic.

## Data model

- `workflows`: definition root. `name` is indexed but intentionally **not**
  unique — multiple versions of a workflow may share a name.
  `version` defaults to `0.1.0`; `status` defaults to `draft`
  (`draft`/`active`/`archived`, enforced by a database CHECK).
- `workflow_steps`: belongs to one workflow (`ON DELETE CASCADE`),
  unique `(workflow_id, name)`, ordered by `position`, carries
  `step_type` and a JSONB `configuration`. A unique `(workflow_id, id)`
  key exists solely as the target for workflow-scoped dependency FKs.
- `workflow_dependencies`: normalized relational edges, not JSON blobs.
  Unique `(from_step_id, to_step_id)` and a database check constraint
  forbidding self-dependencies. **Both endpoints are composite foreign
  keys** — `(workflow_id, from_step_id)` and `(workflow_id, to_step_id)`
  into `workflow_steps(workflow_id, id)` — so an edge can never connect
  steps from two different workflows, even via raw SQL.
- `workflow_runs`: one row per requested execution. `state` starts at
  `pending`; composite index on `(workflow_id, state)`. Phase 7.3 adds
  nullable `schedule_id` (FK → `workflow_schedules.id`,
  `ON DELETE SET NULL` — runs outlive their schedule) and
  `scheduled_for`; a **partial unique index**
  `uq_workflow_runs_schedule_occurrence (schedule_id, scheduled_for)`
  makes duplicate creation of one occurrence impossible at the database
  level.
- `workflow_schedules`: WHEN a run should start (Phase 7.3). One row per
  schedule, bound to one workflow (`ON DELETE CASCADE`). `schedule_type`
  is `once`/`recurring`, with a CHECK keeping shape consistent (`once`
  requires `run_at` and forbids `expression`, recurring the reverse).
  Cron expressions are evaluated in the schedule's own IANA
  `timezone_name`. Lifecycle CHECK: `enabled`/`disabled`/`completed`;
  composite index `(state, next_run_at)` backs due detection.
- `workflow_step_runs`: unique `(run_id, step_id)` — exactly one step-run
  per step per run. Created in topological order at request time, with the
  ordinal persisted in `position`; ordering never relies on timestamps
  (same-transaction inserts share `created_at`).

## Execution states

Both `WorkflowRun` and `StepRun` share the same lifecycle
(`workflows/types.py`):

```
pending → running → succeeded
                  → failed
pending/running → cancelled   (terminal)
succeeded/failed/cancelled    (terminal)
```

The transition table lives in `RUN_STATE_TRANSITIONS`; `can_transition()`
and `is_terminal()` are pure predicates. Phase 7.1 writes only `pending`;
Phase 7.2's engine advances runs and step runs through the full lifecycle,
persisting `output` / `error_message` on step runs (added by migration
`e8b2c4d6f9a3`).

## WorkflowRun vs StepRun

| | WorkflowRun | StepRun |
| --- | --- | --- |
| Represents | One requested execution of a whole workflow | One step's state within one run |
| Children | Many `StepRun`s (one per step) | none |
| Created | By `POST /workflows/{id}/runs` | Atomically with its run |
| Initial state | `pending` | `pending` |

## Execution today (Phase 7.2) and later

Phase 7.2 executes runs **synchronously and sequentially, in-process**:
one engine instance drives one run at a time through ready-step cycles
until a terminal state. The full contract — algorithm, failure sweeps,
cancellation semantics, results — is documented in
[execution.md](execution.md).

Later phases may add a scheduler/worker layer *beside* this stack — never
inside the service:

1. An enqueuer transitions a run `pending → running` and publishes work.
2. Distributed workers consume steps whose dependencies have all
   `succeeded`, honoring topological order and enabling parallelism.
3. Workers record outcomes via the existing transition table; failures use
   `failed` (+ retry policy later).
4. A run finishes when all its `StepRun`s reach a terminal state.

Because ordering is already materialized as relational edges and per-run
step rows, the worker layer can be added without schema changes to the
foundation tables.
