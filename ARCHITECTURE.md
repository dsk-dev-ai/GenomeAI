# GenomeAI Architecture

## Overview

GenomeAI is designed as a layered, modular system where each layer has a well-defined responsibility and communicates through versioned APIs. The architecture prioritizes composability, scalability, and auditability.

> **v1.0.0 status (2026-08-29):** the V1 scope — CLI, REST API,
> Web UI (live demo), Python SDK, workflow DAG engine, 18 external-data
> connectors, and 8 AI analysis services — is **released** and live at
> [genomeai.vercel.app](https://genomeai.vercel.app). Items still marked
> `(Planned)`/`(Future)` below are the longer-term platform vision (HPC,
> gRPC, ML serving, knowledge graph, auth/ABAC, plugins) and are **not** part
> of V1.

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Interfaces                           │
│  CLI   |   REST API   |   gRPC   |   Web UI   |   Notebook SDK   │
└──────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────┴───────────────────────────────────┐
│                        API Gateway / Proxy                        │
│  Auth (ABAC)  |  Rate Limiting  |  Request Validation  |  Audit  │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────┴───────────────────────────────────┐
│                        Orchestration Layer                         │
│  Workflow DAG Engine  |  Job Scheduler  |  Resource Manager       │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌──────────────┬────────────────┼────────────────┬──────────────────┐
│              │                │                │                  │
│  Ingestion   │   Analysis     │   ML Serving   │  Knowledge       │
│  Pipeline    │   Pipeline     │   Engine       │  Graph Service   │
│              │                │                │                  │
│  ┌────────┐  │  ┌──────────┐  │  ┌──────────┐  │  ┌────────────┐  │
│  │FASTQ   │  │  │Variant   │  │  │Model     │  │  │ClinVar     │  │
│  │ BAM    │  │  │Calling   │  │  │Registry  │  │  │GWAS        │  │
│  │ CRAM   │  │  │Quality   │  │  │Training  │  │  │UniProt     │  │
│  │.........│  │  │Control   │  │  │Inference │  │  │PDB         │  │
│  └────────┘  │  │Annotation │  │  │Explain   │  │  │PubMed      │  │
│              │  └──────────┘  │  └──────────┘  │  └────────────┘  │
└──────────────┴────────────────┴────────────────┴──────────────────┘
                                │
┌───────────────────────────────┴───────────────────────────────────┐
│                          Plugin System                             │
│  Hook Registry  |  Sandbox Runtime  |  SDK  |  Marketplace Index  │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────┴───────────────────────────────────┐
│                         Storage Layer                               │
│  Object Store (S3/GCS/MinIO)  |  RDBMS (PostgreSQL)                │
│  Vector DB (pgvector/Milvus)  |  Graph DB  |  File Cache           │
└───────────────────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. User Interfaces

Multiple interface options so users interact with the platform in the way best suited to their workflow:

- **CLI** — Scriptable, CI/CD-friendly command-line tool for all platform operations. ✅ Built (`apps/cli`: `version`, `doctor`).
- **REST API** — JSON/HTTP API for web applications and integrations. ✅ Built (FastAPI, 24 route modules, live).
- **gRPC** — High-performance streaming RPCs for real-time analysis and large data transfers. _(Future)_
- **Web UI** — Browser-based dashboard for monitoring, inspection, and ad-hoc analysis. ✅ Built (Next.js, live demo).
- **Notebook SDK** — Python SDK designed for interactive Jupyter/Lab environments. ✅ Scaffolded (`packages/sdk-python`).

### 2. API Gateway

A single entry point handling cross-cutting concerns:

- **Authentication & Authorization** — Attribute-based access control (ABAC) with support for OAuth 2.0, OIDC, and mTLS. _(Planned)_
- **Rate Limiting** — Per-tenant and per-endpoint quotas. ✅ Built (middleware + AI-provider quotas).
- **Request Validation** — Schema-based validation at the edge. ✅ Built (Pydantic).
- **Audit Logging** — Every mutation is recorded with caller identity, timestamp, and diff. _(Planned)_

### 3. Orchestration Layer

The brain of the platform, responsible for executing genomic workflows as directed acyclic graphs (DAGs):

- **Workflow DAG Engine** — Defines analysis steps and their dependencies. Supports checkpointing, retry, and partial re-execution. ✅ Built (Phases 7.1–7.6).
- **Cron Scheduler** — Application-level due-run detection with timezone support. ✅ Built (Phase 7.3).
- **Redis Queue Worker** — Background execution with claim/release, graceful shutdown. ✅ Built (Phase 7.4).
- **Parallel Execution** — Concurrent execution of independent steps via structured concurrency. ✅ Built (Phase 7.6).
- **Retry & Failure** — Failure classification, configurable retry policies, backoff. ✅ Built (Phase 7.5).
- **Job Scheduler** — Distributes work across available compute resources. Pluggable backends (HPC, Kubernetes). _(Planned)_
- **Resource Manager** — Tracks and allocates CPU, GPU, memory, and storage across concurrent analyses. _(Future)_

Workflows are expressed in a YAML specification. See [docs/architecture/](docs/architecture/) for the design document.

### 4. Core Services

#### Ingestion Pipeline

Handles raw sequencing data from multiple sources:

- Supports FASTQ, BAM, CRAM, VCF, and HDF5 formats. _(Planned)_
- Automatic quality control and adapter trimming. _(Planned)_
- Pluggable aligners (BWA-MEM2, Minimap2, STAR). _(Planned)_
- Deduplication, base quality score recalibration. _(Planned)_
- Streaming mode for real-time nanopore data. _(Future)_

#### Analysis Pipeline

Primary bioinformatics analysis modules:

- **Variant Calling** — Germline (GATK, DeepVariant) and somatic (Mutect2, Strelka2). _(Planned)_
- **Quality Control** — Per-sample and per-cohort QC reports (FastQC, MultiQC). _(Planned)_
- **Annotation** — Variant annotation against Ensembl, RefSeq, ClinVar, dbSNP. _(Planned)_
- **RNA-seq** — Quantification (Salmon, Kallisto), differential expression (DESeq2, limma). _(Planned)_
- **Single Cell** — Clustering, trajectory inference, integration (Scanpy, Seurat interop). _(Future)_

#### ML Serving Engine

- **Model Registry** — Versioned storage of trained models with metadata (training data, hyperparameters, performance metrics). _(Future)_
- **Training Pipeline** — Distributed training orchestration with GPU support. _(Future)_
- **Inference Service** — Low-latency prediction with batching and caching. _(Future)_
- **Explainability** — SHAP, LIME, and attention-based attribution built into the inference path. _(Future)_

#### Knowledge Graph Service

A continuously updated biomedical knowledge graph:

- **Sources** — ClinVar, GWAS Catalog, UniProt/Swiss-Prot, PDB, PubMed, COSMIC, ENCODE. _(Planned)_
- **Query** — SPARQL endpoint, graph traversal API, and vector similarity search. _(Planned)_
- **Embeddings** — Node and edge embeddings for ML integration. _(Future)_
- **Versioning** — Immutable snapshots with changelog between releases. _(Planned)_

### 5. Plugin System

The plugin system allows the community to extend any layer without modifying core code.

- **Hook Registry** — Well-defined extension points (before/after alignment, custom annotation, custom model architectures, etc.). _(Planned)_
- **Sandbox Runtime** — Plugins execute in isolated containers with resource limits. _(Planned)_
- **SDK** — Python and Rust SDKs for plugin development. _(Planned)_
- **Marketplace Index** — A registry of community plugins with versioning and dependency resolution. _(Future)_

See [docs/plugins/](docs/plugins/) for plugin development guides.

### 6. Storage Layer

- **Object Store** — Immutable storage for raw and processed genomic data. Supports S3, GCS, Azure Blob, and MinIO. _(Planned)_
- **RDBMS** — PostgreSQL 16+ with schemas for samples, analyses, workflows, and access control. _(Planned)_
- **Vector DB** — pgvector extension or Milvus for embedding similarity search. _(Planned)_
- **Graph DB** — Knowledge graph storage (Apache AGE or custom). _(Future)_
- **File Cache** — Local and distributed caching for frequently accessed reference data. _(Planned)_

## Data Flow (Target Design)

```
1. User submits a sequencing run (FASTQ files) via CLI or API.
2. Gateway authenticates the request and validates the input manifest.
3. Orchestrator constructs a DAG: QC → Align → Sort → Mark Duplicates → BQSR → Variant Call → Annotate.
4. Each step reads from object store, processes in a container, writes results back to object store.
5. Metadata (sample, run parameters, QC metrics) is written to PostgreSQL.
6. Annotated variants are indexed in the knowledge graph for query.
7. ML models can consume variant calls and graph features for downstream prediction.
8. Everything is logged and traceable via a global request ID.
```

> v1.0 data flow is live: connectors → cache → AI analysis → enhanced REST endpoints; CLI/SDK are scaffolded, HPC/ML/knowledge-graph components are the future platform vision.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Workflows as DAGs | Enables checkpointing, partial re-execution, and parallelization. ✅ Implemented. |
| PostgreSQL as source of truth | Reliable, well-understood, excellent ecosystem. ✅ Implemented. |
| Pluggable aligners/callers | No single tool dominates; researchers need choice. |
| ABAC over RBAC | Genomic data has complex access patterns (by study, by consent, by institution). |
| Plugin sandboxing | Prevents malicious or buggy plugins from compromising the platform. |
| Free APIs first | NCBI, Ensembl, UniProt, ClinVar, gnomAD — all free, no keys required. ✅ Implemented (18 connectors). |
| Cost-effective AI (Gemini + Ollama) | Gemini cloud default (`gemini-3.6-flash`) for quality; Ollama for zero-cost, privacy-preserving local analysis. |
| Structured concurrency | TaskGroup + Semaphore for safe parallel execution (Phase 7.6). ✅ Implemented. |

## Key Technologies

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Core services | Python 3.12, FastAPI | FastAPI ecosystem, async support, type safety |
| Data models | SQLAlchemy, Pydantic | ORM + schema validation, migration support |
| Database | PostgreSQL 16+, Redis 7+ | ACID, full-text search, queue, caching |
| Orchestration | Custom DAG engine | Parallel execution, retry, scheduling (Phases 7.1–7.6) |
| Frontend | Next.js, React, TypeScript | SSR, component ecosystem, type safety |
| Visualization | D3.js, Three.js, Cytoscape.js, Mol* | Genome browser, 3D structures, network graphs |
| AI/LLM | Gemini (default `gemini-3.6-flash`), Ollama (local) | Cloud default + zero-cost local option |
| Vector search | pgvector | Simplicity of a single database |
| DevOps | Docker, GitHub Actions, Turbo | Containerization, CI/CD, monorepo builds |

## Related Documents

- [API design](docs/api/)
- [Database schema](docs/database/)
- [Plugin SDK](docs/plugins/)
- [Deployment architecture](docs/deployment/)
- [Architecture Decision Records](docs/decisions/)
