# Workflow Foundation (Phase 7.1)

The Workflow Foundation establishes GenomeAI's workflow/DAG architecture:
workflow definitions, ordered and connected steps, deterministic DAG
validation, execution-state models, persistence, and a minimal admin API.

> **Phase 7.1 does NOT execute workflows.** Runs are created in the
> `pending` state with pending step runs, and nothing ever advances them.
> There is no scheduler, queue, worker, or parallel execution engine —
> those belong to Phase 7.2+.

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

## What does NOT exist yet

- No background execution, scheduler, or workers
- No Redis/Celery/Arq queues, no parallel engine, no retries
- No artifact storage, caching, or result capture
- Step `configuration` payloads are stored but never interpreted

See [architecture.md](architecture.md) for the planned execution design.
