# ADR 005: Core Implementation Languages

**Status:** Superseded (2026-08-29) — see below.

## Context

GenomeAI spans high-performance genomic data processing, machine learning, and web services. The choice of programming languages impacts performance, developer productivity, community contributions, and ecosystem access.

## Decision (superseded)

This ADR originally chose **Rust** for the platform core and **Python** for the
data science and ML layer, with TypeScript for the web UI.

**As released in v1.0.0, the implemented stack is fully Python + TypeScript:**
- **Python** (FastAPI, SQLAlchemy, asyncio) — backend, workflow DAG engine,
  integration connectors, AI services, CLI, SDK.
- **TypeScript** (Next.js, React) — web UI and TS SDK.
- No Rust in the codebase. The project favors Python's ecosystem (Biopython,
  pydantic, asyncio) and TypeScript for the web layer; HPC kernels (aligners,
  variant callers) are invoked as external tools (e.g. minimap2, GATK) rather
  than reimplemented in Rust.

## Original rationale (kept for history)

### Core Platform (Rust)

- Workflow DAG engine
- Ingestion pipeline (FASTQ parsing, alignment orchestration)
- API gateway and request routing
- Storage layer clients
- Plugin sandbox runtime

### Data Science Layer (Python)

- Analysis pipeline wrappers (variant calling, RNA-seq, single-cell)
- ML model training and inference
- Knowledge graph population and query
- CLI tool
- SDK and notebook integration

### Cross-Cutting

- **Protobuf** for service contract definitions.
- **YAML** for workflow and configuration files.
- **TypeScript** (optional) for web UI (separate repository).

## Consequences

**Positive:**
- Rust provides memory safety and C-level performance for hot paths.
- Python provides rich ecosystem for bioinformatics (Biopython, PySam, scikit-learn, PyTorch).
- Clear separation of concerns: performance-critical vs. flexibility-critical.
- Broad contributor base: Rust and Python are both popular.

**Negative:**
- Cross-language communication overhead (FFI or gRPC).
- Requires expertise in both languages from core maintainers.
- Build system complexity: Rust's Cargo and Python's setuptools/poetry.

## Alternatives Considered

1. **All Python** — Performance ceiling for genomic data processing at population scale.
2. **All Rust** — Impractical for ML ecosystem; Python is dominant.
3. **Go + Python** — Go is performant but lacks Rust's safety guarantees for concurrent data structures.
4. **C++ + Python** — Memory safety concerns in C++ without compensating benefits over Rust.
