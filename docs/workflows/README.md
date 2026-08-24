# Workflow Foundation (Phase 7.1) & Execution (Phase 7.2)

The Workflow Foundation establishes GenomeAI's workflow/DAG architecture:
workflow definitions, ordered and connected steps, deterministic DAG
validation, execution-state models, persistence, and a minimal admin API.
Phase 7.2 adds deterministic, sequential, **in-process** execution on top.

> Execution is synchronous: one API call drives one run step by step to a
> terminal state. There is still no scheduler, queue, worker, or parallel
> execution engine — those belong to later milestones.

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

## What does NOT exist yet

- No background execution, scheduler, or workers
- No Redis/Celery/Arq queues, no parallel engine, no retries
- No artifact storage, caching beyond step outputs, or real executors —
  step execution is still a deterministic passthrough placeholder
