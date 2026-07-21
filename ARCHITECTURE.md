# GenomeAI Architecture

## Overview

GenomeAI is designed as a layered, modular system where each layer has a well-defined responsibility and communicates through versioned APIs. The architecture prioritizes composability, scalability, and auditability.

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

- **CLI** — Scriptable, CI/CD-friendly command-line tool for all platform operations. _(Planned)_
- **REST API** — JSON/HTTP API for web applications and integrations. _(Planned)_
- **gRPC** — High-performance streaming RPCs for real-time analysis and large data transfers. _(Future)_
- **Web UI** — Browser-based dashboard for monitoring, inspection, and ad-hoc analysis. _(Future)_
- **Notebook SDK** — Python SDK designed for interactive Jupyter/Lab environments. _(Future)_

### 2. API Gateway

A single entry point handling cross-cutting concerns:

- **Authentication & Authorization** — Attribute-based access control (ABAC) with support for OAuth 2.0, OIDC, and mTLS. _(Planned)_
- **Rate Limiting** — Per-tenant and per-endpoint quotas. _(Planned)_
- **Request Validation** — Schema-based validation at the edge. _(Planned)_
- **Audit Logging** — Every mutation is recorded with caller identity, timestamp, and diff. _(Planned)_

### 3. Orchestration Layer

The brain of the platform, responsible for executing genomic workflows as directed acyclic graphs (DAGs):

- **Workflow DAG Engine** — Defines analysis steps and their dependencies. Supports checkpointing, retry, and partial re-execution. _(Planned)_
- **Job Scheduler** — Distributes work across available compute resources. Pluggable backends (local, HPC, Kubernetes). _(Planned)_
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

> This is the target data flow for the v1.0 release. Not all components are implemented yet.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Workflows as DAGs | Enables checkpointing, partial re-execution, and parallelization. |
| Object store as source of truth | Decouples compute from storage; enables spot instance usage. |
| Pluggable aligners/callers | No single tool dominates; researchers need choice. |
| ABAC over RBAC | Genomic data has complex access patterns (by study, by consent, by institution). |
| Plugin sandboxing | Prevents malicious or buggy plugins from compromising the platform. |

## Key Technologies

| Layer | Technology (Proposed) | Rationale |
|-------|---------------------|-----------|
| Core services | Rust | Performance, memory safety, and zero-cost abstractions for hot paths. |
| Data science layer | Python | Dominant language in bioinformatics and ML. |
| Orchestration | Custom DAG engine | Specialized for genomic workflows (checkpointing, resume). |
| Storage | PostgreSQL + Object Store | Reliable, well-understood, excellent ecosystem. |
| Vector search | pgvector | Simplicity of a single database; fallback to Milvus at scale. |
| Container runtime | OCI-compatible (Docker, Podman) | Universal, well-sandboxed. |

## Related Documents

- [API design](docs/api/)
- [Database schema](docs/database/)
- [Plugin SDK](docs/plugins/)
- [Deployment architecture](docs/deployment/)
- [Architecture Decision Records](docs/decisions/)
