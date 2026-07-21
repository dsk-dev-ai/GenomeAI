# GenomeAI Roadmap

This document describes the planned development roadmap. Milestones and priorities are revised based on community feedback and emerging research needs.

## Legend

- 📋 Planned
- 🚧 In Progress
- ✅ Released

---

## Phase 0: Foundation (v0.1 — Current)

**Goal:** Repository infrastructure, architectural blueprint, and community tooling.

| Milestone | Status |
|-----------|--------|
| Repository foundation, documentation, governance | 📋 |
| CI/CD pipeline and contribution tooling | 📋 |
| Development environment setup guide | 📋 |
| Plugin SDK specification (design doc) | 📋 |
| Workflow DAG engine design | 📋 |

## Phase 1: Core Pipelines (v0.2–v0.5)

**Goal:** Establish ingestion, basic analysis, and storage layers.

| Milestone | Target Version | Status |
|-----------|---------------|--------|
| FASTQ/BAM ingestion pipeline with quality control | v0.2 | 📋 |
| Workflow DAG engine — single-node execution | v0.2 | 📋 |
| PostgreSQL schema for samples and analyses | v0.2 | 📋 |
| CLI tool with basic commands | v0.3 | 📋 |
| Variant calling pipeline (germline WGS/WES) | v0.3 | 📋 |
| Containerized deployment with Docker Compose | v0.3 | 📋 |
| REST API v1 (samples, analyses, workflows) | v0.4 | 📋 |
| Knowledge graph v1 (ClinVar, dbSNP, Ensembl) | v0.4 | 📋 |
| RNA-seq quantification and differential expression | v0.5 | 📋 |
| Multi-node workflow execution (Kubernetes) | v0.5 | 📋 |

## Phase 2: Scale (v1.0)

**Goal:** Production-ready platform at population scale.

| Milestone | Status |
|-----------|--------|
| Single-cell RNA-seq pipeline | 📋 |
| Somatic variant calling | 📋 |
| ML training pipeline v1 (variant effect prediction) | 📋 |
| Knowledge graph v2 (UniProt, PDB, GWAS Catalog, COSMIC) | 📋 |
| Federated identity and ABAC enforcement | 📋 |
| Cohort-level QC and population statistics | 📋 |
| gRPC API for streaming data transfer | 📋 |
| Plugin marketplace and dependency resolution | 📋 |
| Audit logging and compliance reporting | 📋 |
| Performance benchmarks: 10,000 WGS on 1,000-core cluster | 📋 |
| Differential privacy primitives | 📋 |

## Phase 3: Intelligence (v2.0)

**Goal:** AI-native analysis with explainable predictions and automated discovery.

| Milestone | Status |
|-----------|--------|
| Foundation model for regulatory genomics (DNA sequences) | 📋 |
| Graph neural network training on knowledge graph | 📋 |
| LLM-based analysis assistant grounded in knowledge graph | 📋 |
| Automated hypothesis generation from cohort signals | 📋 |
| Clinical decision support module (variant interpretation) | 📋 |
| Multi-modal integration (genomics + transcriptomics + proteomics) | 📋 |
| Federated learning across institutional boundaries | 📋 |

## Phase 4: Ecosystem (v3.0+)

**Goal:** A global, open genomic intelligence network.

| Milestone | Status |
|-----------|--------|
| Whole-genome simulation and perturbation engine | 📋 |
| EHR integration framework (FHIR) | 📋 |
| Real-time population surveillance pipelines | 📋 |
| Public data exchange with consent management | 📋 |
| Global genomic intelligence network | 📋 |

---

## How Milestones Are Set

1. **Community input** — Feature requests with broad support are prioritized.
2. **Research impact** — Milestones that unblock significant research are fast-tracked.
3. **Technical dependency** — Foundational work must precede dependent features.
4. **Maintainability** — Debt is addressed alongside feature work, not deferred indefinitely.

See [GOVERNANCE.md](GOVERNANCE.md) for how roadmap decisions are made.

## Track Progress

- [GitHub Issues](https://github.com/dsk-dev-ai/GenomeAI/issues)
- [Milestones](https://github.com/dsk-dev-ai/GenomeAI/milestones)
- [Discussions](https://github.com/dsk-dev-ai/GenomeAI/discussions)
