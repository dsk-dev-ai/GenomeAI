# ADR 001: Workflow DAG Engine Core

**Status:** Accepted (updated to reflect implementation)

## Context

Genomic analyses consist of multiple steps (QC, alignment, sorting, variant calling, annotation) with complex dependencies. Existing solutions (Nextflow, Snakemake, Cromwell) are external dependencies with their own ecosystems and limitations. We need a workflow engine that is tightly integrated with GenomeAI's data model and can support checkpointing, partial re-execution, and streaming inputs.

## Decision

Build a custom DAG-based workflow engine as a core GenomeAI component.

### Key Design Choices (as implemented)

- Workflows are defined via REST API (JSON payloads) with explicit step
  dependencies resolved by name. Steps carry `step_type` and a JSONB
  `configuration` blob — no YAML, no OCI containers in this phase.
- Each step is executed by a pluggable `StepExecutor` abstraction; the
  default `PassthroughStepExecutor` is deterministic for testing. Real
  biological executors will plug in via the same interface.
- Intermediate results are stored as JSONB on `workflow_step_runs.output`
  — no object store in this phase. Checkpointing and partial
  re-execution are deferred.
- The engine supports failure propagation: a failing step cancels all
  downstream dependents. Retries are workflow-level (Phase 7.5) with
  configurable failure classification and backoff.
- Workflow state is persisted in PostgreSQL for observability and audit.
  The engine is single-process and single-run; parallel concurrent
  execution of independent steps is supported via `max_concurrency`
  (Phase 7.6).
- Scheduling is application-level (Phase 7.3): cron-based due-run
  detection, not a distributed scheduler. Background execution uses a
  Redis queue with a single worker process (Phase 7.4).

### What was deferred vs. the original plan

| Original plan | Actual implementation | Deferred to |
|---|---|---|
| YAML definitions | REST API (JSON) | — |
| OCI container steps | In-process `StepExecutor` | Later phases |
| Object store for intermediates | JSONB on step runs | Later phases |
| Partial re-execution | Full-run execution only | Later phases |
| Pluggable schedulers (HPC/K8s) | Application-level cron scheduler | Phase 2+ |
| Kubernetes multi-node | Single-process worker | Phase 1 v0.5 |

## Consequences

**Positive:**
- Deep integration with GenomeAI's data and access control models.
- No external workflow engine dependency.
- Deterministic, testable execution (2,150+ tests passing).
- Parallel execution of independent steps (Phase 7.6).
- Retry/failure classification with configurable policies (Phase 7.5).

**Negative:**
- No partial re-execution yet — a failed workflow must re-run from scratch.
- Single-process only — no distributed execution or autoscaling.
- JSONB outputs limited in size compared to object store.

## Alternatives Considered

1. **Nextflow integration** — Powerful, but DSL complexity and JVM dependency.
2. **Snakemake** — Python-native, but limited execution model and scaling.
3. **Apache Airflow** — Good for orchestration, but not designed for data-heavy genomic workflows.
4. **Reuse existing DAG libraries (Dask, Prefect)** — Evaluated; insufficient control over checkpoint semantics.
