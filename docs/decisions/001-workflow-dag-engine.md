# ADR 001: Workflow DAG Engine Core

**Status:** Accepted

## Context

Genomic analyses consist of multiple steps (QC, alignment, sorting, variant calling, annotation) with complex dependencies. Existing solutions (Nextflow, Snakemake, Cromwell) are external dependencies with their own ecosystems and limitations. We need a workflow engine that is tightly integrated with GenomeAI's data model and can support checkpointing, partial re-execution, and streaming inputs.

## Decision

Build a custom DAG-based workflow engine as a core GenomeAI component.

### Key Design Choices

- Workflows are defined in YAML with explicit step dependencies.
- Each step is an OCI container with versioned inputs and outputs.
- Intermediate results are stored in the object store, enabling checkpointing.
- The engine supports partial re-execution: if step N fails, only N and downstream steps are re-run after the fix.
- Workflow state is persisted in PostgreSQL for observability and audit.
- Pluggable schedulers: local process pool, HPC (Slurm/PBS), Kubernetes.

## Consequences

**Positive:**
- Deep integration with GenomeAI's data and access control models.
- No external workflow engine dependency.
- Fine-grained checkpointing and resume semantics.
- Single interface for all workflow operations.

**Negative:**
- Significant implementation effort.
- Requires maintaining a custom scheduler abstraction.
- Re-inventing functionality that mature tools already provide.

## Alternatives Considered

1. **Nextflow integration** — Powerful, but DSL complexity and JVM dependency.
2. **Snakemake** — Python-native, but limited execution model and scaling.
3. **Apache Airflow** — Good for orchestration, but not designed for data-heavy genomic workflows.
4. **Reuse existing DAG libraries (Dask, Prefect)** — Evaluated; insufficient control over checkpoint semantics.
