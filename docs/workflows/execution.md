# Workflow Execution (Phase 7.2)

Phase 7.2 adds a **deterministic, sequential, in-process** DAG execution
engine on top of the Phase 7.1 foundation.

> **This is NOT a distributed engine.** There is no Redis/Celery/Arq
> queue, no scheduler, no background workers, no parallelism, no retries,
> no caching, and no artifact storage. One HTTP call executes one run,
> step by step, before responding.

## Architecture

```
POST /workflows/runs/{run_id}/execute        routes/workflows.py (thin)
  ↓
DAGExecutionEngine      workflows/execution/engine.py   ← orchestration
  ├── planner           workflows/execution/planner.py  ← pure ready-step math
  ├── StepExecutor      workflows/execution/executor.py ← one step's work
  └── WorkflowRepository                                ← persistence only
```

Separation of concerns (unchanged responsibilities from 7.1):

| Component | Owns | Never does |
| --- | --- | --- |
| `WorkflowService` | definition validation, run initialization | execution |
| `DAGExecutionEngine` | run/step state transitions, scheduling order, failure & cancellation sweeps | step work itself |
| `StepExecutor` | executing ONE step and returning a result | persistence, transitions |
| Planner (`ready_steps`) | which steps are eligible right now | I/O of any kind |
| Repository | persisting state changes | deciding legality |

The engine is not coupled to FastAPI: it takes any object satisfying the
`ExecutionRunStore` protocol (the real `WorkflowRepository` does), a
`StepExecutor`, and an optional cancellation predicate.

## Execution algorithm

For a run in `pending` state:

1. **Load** the run (404 if unknown) and reject non-pending runs with
   `WorkflowStateTransitionError` (HTTP 409) — runs execute exactly once.
2. **Validate the stored graph** with the same `validate_graph` used at
   definition time *before* transitioning anything. A broken graph leaves
   the run untouched (`pending`) and raises `WorkflowValidationError`.
3. `pending → running`; `started_at` is stamped.
4. Loop:
   - If the cancellation predicate fires: every never-started `StepRun`
     becomes `cancelled` (completed steps are preserved), then
     `running → cancelled`. Return.
   - Ask the planner for ready steps: `pending` steps whose direct
     upstream all `succeeded`, in persisted `position` order.
   - Execute the first ready step via the injected `StepExecutor`,
     passing its direct predecessors' outputs.
   - On success: record `output` on the `StepRun`, continue.
   - On failure: record `error_message` on the `StepRun`, sweep all
     remaining `pending` step runs to `cancelled`, transition
     `running → failed`, and preserve the reason on both the `StepRun`
     and the `WorkflowRun`. **No retries.**
5. When nothing is ready and everything `succeeded`:
   `running → succeeded`.

Cancellation is also honoured **before** the first transition: a pending
run goes straight to `cancelled` with all step runs cancelled.

## Results

- Success output is stored on `workflow_step_runs.output` (JSONB).
- Failure reasons are stored on `workflow_step_runs.error_message` and
  mirrored onto `workflow_runs.error_message`
  (`"Step '<name>' failed: <reason>"`).
- There is no artifact storage; outputs must stay JSON-serializable.

## The default executor

`PassthroughStepExecutor` is a deterministic placeholder that exists so
the engine is testable end-to-end without real domain logic:

- Fails iff its configuration contains the key `fail_with_message`
  (value becomes the error message).
- Otherwise succeeds, emitting the merge of direct upstream outputs —
  applied in name order so later names win conflicts — overridden by its
  own configuration.

Real executors implement the `StepExecutor` ABC — they receive the
persisted `WorkflowStep` plus a `StepExecutionContext` (run/workflow ids,
workflow name, upstream outputs) and return a `StepExecutionResult`.

## API

```
POST /workflows/runs/{run_id}/execute → 200 WorkflowRunResponse (terminal)
                                        404 unknown run
                                        409 non-pending run
```

The call is **synchronous**: the response only returns once the run has
reached a terminal state (`succeeded`, `failed`, or `cancelled`).

## What Phase 7.2 intentionally does NOT do

- No queues/schedulers/workers (Redis, Celery, Arq, …)
- No distributed or parallel execution — strictly one step at a time
- No retries, timeouts, heartbeats, or caching
- No artifact/blob storage
- No new background infrastructure of any kind

These belong to later milestones; the engine's seams (planner purity,
executor abstraction, repository-only persistence) exist so they can be
introduced without reworking this layer.
