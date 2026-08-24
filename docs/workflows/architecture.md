# Workflow Architecture

```
API (FastAPI, /workflows)
 ↓
WorkflowService          ← DAG validation, run initialization (no execution)
 ↓
WorkflowRepository       ← persistence only
 ↓
SQLAlchemy models        ← workflows / workflow_steps / workflow_dependencies /
                            workflow_runs / workflow_step_runs
 ↓
PostgreSQL
```

## Layers

- **Routes** (`routes/workflows.py`): thin HTTP surface. Pydantic schemas in,
  response schemas out. Typed domain errors are mapped centrally in
  `main.py` (`WorkflowValidationError` → 422 with an `issues` list;
  not-found errors → 404).
- **Service** (`services/workflow.py`): owns definition validation and run
  initialization. It validates the submitted graph **before** persisting and
  computes a deterministic topological order when a run is requested.
  The service never executes steps — Phase 7.1 has no execution engine.
- **Repository** (`repositories/workflow.py`): persistence only. Creates
  workflows with eagerly generated step ids so dependency edges can be
  resolved by name before the flush; creates runs plus one pending
  `StepRun` per step.
- **Domain** (`workflows/dag.py`, `workflows/types.py`, `workflows/errors.py`):
  pure functions and typed vocabulary. No I/O, fully deterministic.

## Data model

- `workflows`: definition root. `name` is indexed but intentionally **not**
  unique — multiple versions of a workflow may share a name.
  `version` defaults to `0.1.0`; `status` defaults to `draft`
  (`draft`/`active`/`archived`).
- `workflow_steps`: belongs to one workflow (`ON DELETE CASCADE`),
  unique `(workflow_id, name)`, ordered by `position`, carries
  `step_type` and a JSONB `configuration`.
- `workflow_dependencies`: normalized relational edges, not JSON blobs.
  Unique `(from_step_id, to_step_id)` and a database check constraint
  forbidding self-dependencies. Both endpoints are FKs into
  `workflow_steps`. Same-workflow integrity is enforced at the application
  level: the service only ever creates edges between steps it just created
  for that workflow.
- `workflow_runs`: one row per requested execution. `state` starts at
  `pending`; composite index on `(workflow_id, state)`.
- `workflow_step_runs`: unique `(run_id, step_id)` — exactly one step-run
  per step per run. Created in topological order at request time.

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
the transition machinery exists so the model is complete and testable.

## WorkflowRun vs StepRun

| | WorkflowRun | StepRun |
| --- | --- | --- |
| Represents | One requested execution of a whole workflow | One step's state within one run |
| Children | Many `StepRun`s (one per step) | none |
| Created | By `POST /workflows/{id}/runs` | Atomically with its run |
| Initial state | `pending` | `pending` |

## Future execution design (Phase 7.2+, NOT implemented)

Later phases will add a scheduler/worker layer *beside* this stack — never
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
