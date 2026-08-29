<p align="center">
  <a href="https://genomeai.vercel.app"><img src="https://img.shields.io/badge/Live_Demo-View_Online-2ea44f?style=for-the-badge&logo=internetexplorer&logoColor=white" alt="Live Demo"/></a>
  <a href="https://github.com/dsk-dev-ai/GenomeAI/stargazers"><img src="https://img.shields.io/github/stars/dsk-dev-ai/GenomeAI?style=for-the-badge&logo=github&color=yellow" alt="GitHub Stars"/></a>
  <a href="https://github.com/dsk-dev-ai/GenomeAI/forks"><img src="https://img.shields.io/github/forks/dsk-dev-ai/GenomeAI?style=for-the-badge&logo=github" alt="Forks"/></a>
</p>

<p align="center">
  <a href="https://github.com/dsk-dev-ai/GenomeAI/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/dsk-dev-ai/GenomeAI/actions"><img src="https://img.shields.io/github/actions/workflow/status/dsk-dev-ai/GenomeAI/ci.yml?style=flat-square&label=CI" alt="CI Status"></a>
  <a href="https://github.com/dsk-dev-ai/GenomeAI/last-commit"><img src="https://img.shields.io/github/last-commit/dsk-dev-ai/GenomeAI?style=flat-square&label=Last%20commit" alt="Last commit"></a>
  <a href="https://github.com/dsk-dev-ai/GenomeAI/issues"><img src="https://img.shields.io/github/issues/dsk-dev-ai/GenomeAI?style=flat-square" alt="Open issues"></a>
  <a href="https://github.com/dsk-dev-ai/GenomeAI/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome"></a>
  <a href="https://github.com/sponsors/dsk-dev-ai"><img src="https://img.shields.io/badge/%E2%9D%A4%EF%B8%8F-Sponsor-red?style=flat-square&logo=githubsponsors&logoColor=white" alt="Sponsor"></a>
</p>

<h1 align="center">🧬 GenomeAI</h1>

<p align="center">
  <strong>Open-source AI platform for genomics, bioinformatics, biomedical research,<br/>and evidence-based AI powered by public scientific databases and multi-provider LLMs.</strong>
</p>

<p align="center">
  <a href=".github/genomeai-og.png"><img src=".github/genomeai-og.png" alt="GenomeAI banner" width="100%"/></a>
</p>

## 🚀 Live Demo

> **Try GenomeAI right now — no install required.** Click the link and use the
> working application:

<p align="center">
  <a href="https://genomeai.vercel.app"><strong>🌐 Open the Live Demo → https://genomeai.vercel.app</strong></a>
  <br/>
  <sub>Backend API: <code>https://genomeai-api.onrender.com</code> · free-tier hosts, deployed automatically on every release.
  See <a href="docs/deployment/releases.md">docs/deployment/releases.md</a> for how it works.</sub>
</p>

---

## What is GenomeAI?

GenomeAI is a unified platform that brings together **public biological databases**, **workflow automation**, **data visualization**, and **AI-powered analysis** — all in one open-source stack.

It connects directly to 37+ free public APIs (NCBI, Ensembl, UniProt, PubChem, PubMed, gnomAD, ClinVar, AlphaFold, and more) to give researchers instant access to genomic, proteomic, chemical, and clinical data — without expensive licenses or proprietary infrastructure.

**Goal:** Make biomedical research accessible, reproducible, and AI-augmented for every researcher, clinician, and developer — anywhere in the world.

---

## Why GenomeAI?

| Problem | GenomeAI Solution |
|---------|-------------------|
| Biomedical data is scattered across 100+ databases | Unified connector layer — one API for all sources |
| Existing tools require expensive licenses | 100% open-source, runs on free-tier APIs |
| No integrated AI for genomic analysis | Multi-provider LLM support (Ollama, Groq, Together, OpenAI, Claude) |
| Workflows are manual and error-prone | DAG-based workflow engine with retry, scheduling, and parallel execution |
| Results are hard to visualize | Built-in genome browser, protein viewer, network graphs, scientific charts |
| Reproducibility is difficult | Versioned workflows, provenance tracking, audit logs |

---

## Features

### Built and Working

| Feature | Status | PRs |
|---------|--------|-----|
| Biological domain models (Genome, Sample, Gene, Variant, Transcript) | ✅ | #7–#22 |
| REST API with CRUD endpoints | ✅ | #7–#22 |
| Workflow DAG engine (definitions, steps, dependencies, validation) | ✅ | #42 |
| Deterministic sequential execution | ✅ | #43 |
| Cron-based workflow scheduler | ✅ | #44 |
| Queue & worker (Redis-backed background execution) | ✅ | #45 |
| Retry & failure handling (classification, backoff, policies) | ✅ | #46 |
| Parallel DAG execution (concurrent independent steps) | ✅ | #47 |
| Data integration foundation (sources, fetchers, connectors) | ✅ | #41 |
| Genome browser, protein viewer, network graphs, scientific charts | ✅ | #28–#40 |

### Coming Next

| Feature | Phase |
|---------|-------|
| NCBI, Ensembl, UniProt, PubMed connector integration | 4 |
| Variant annotation pipeline (ClinVar, gnomAD, dbSNP) | 4 |
| Drug-target and compound data (ChEMBL, PubChem, DrugBank) | 4 |
| AI-powered literature search and summarization | 5 |
| Knowledge graph (gene-disease-drug-protein associations) | 5 |
| LLM analysis assistant (variant interpretation, report generation) | 6 |
| Multi-provider AI gateway (Ollama, Groq, OpenAI, Claude) | 6 |
| Plugin SDK and marketplace | 7 |

---

## Public Data Sources (Free APIs)

GenomeAI connects to **37+ free public databases** across 12 categories:

| Category | Sources | Auth Required? |
|----------|---------|----------------|
| **Genomic** | NCBI E-utilities, Ensembl REST, UCSC, gnomAD, ClinVar, dbSNP | No (API key optional for higher rate) |
| **Protein** | UniProt, RCSB PDB, AlphaFold DB | No |
| **Drug/Compound** | ChEMBL, PubChem, RxNorm, OpenFDA | No |
| **Literature** | PubMed, Europe PMC, Semantic Scholar | No |
| **Clinical** | ClinicalTrials.gov, OMIM | No |
| **Pathway** | Reactome, KEGG, Gene Ontology (AmiGO) | No |
| **Disease** | Disease Ontology, MONDO, Orphanet | No |
| **Expression** | GTEx, ENCODE | No |
| **Variant** | ClinVar, gnomAD, LOVD, GWAS Catalog | No |
| **Chemical** | PubChem, ChEMBL, PDB Ligands | No |
| **Network** | STRING, BioGRID | No |
| **Ontology** | HPO, Disease Ontology, Gene Ontology | No |

See [docs/external-data/MASTER_PLAN.md](docs/external-data/MASTER_PLAN.md) for the full integration plan.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
│         CLI   |   REST API   |   Web UI   |   Python SDK         │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│           Auth  |  Rate Limiting  |  Validation  |  Audit        │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                      Orchestration Layer                         │
│  Workflow DAG Engine  |  Cron Scheduler  |  Redis Queue Worker   │
│  (parallel exec)      |  (scheduling)    |  (retry, backoff)    │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────┬───────────────┼───────────────┬───────────────────┐
│              │               │               │                   │
│  Biological  │   Data        │   AI/LLM      │   Visualization   │
│  Domains     │   Integration │   Gateway     │   Platform        │
│              │               │               │                   │
│  Genome      │   NCBI        │   Ollama      │   Genome Browser  │
│  Sample      │   Ensembl     │   Groq        │   Protein Viewer  │
│  Gene        │   UniProt     │   Together    │   Network Graphs  │
│  Variant     │   PubMed      │   OpenAI      │   Scientific      │
│  Transcript  │   PubChem     │   Claude      │   Charts          │
│  Protein     │   ChEMBL      │   Local       │   3D Molecular    │
│              │   gnomAD      │               │                   │
└──────────────┴───────────────┴───────────────┴───────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                          Storage Layer                            │
│           PostgreSQL  |  Redis  |  Object Storage                 │
└──────────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full technical breakdown.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dsk-dev-ai/GenomeAI.git
cd GenomeAI

# Install all dependencies and start infrastructure
make setup

# Run tests (2051 passing)
make test

# Start the API server
uvicorn genomeai_api.main:app --reload
```

**Requirements:** Python 3.12+, Node.js 20+, PostgreSQL 16+, Redis 7+

See [docs/development/](docs/development/) for detailed setup guides.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL 16+, Redis 7+ |
| Workflow Engine | Python asyncio, DAG execution, Redis queue |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Visualization | D3.js, Three.js, Cytoscape.js, Mol* |
| AI/LLM | Ollama (local), Groq, Together AI, OpenAI, Anthropic |
| DevOps | Docker, GitHub Actions, Turbo (monorepo) |
| Testing | pytest (2051 tests), biome, ruff, pyright |

---

## Documentation

| Topic | Location |
|-------|----------|
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |
| API Reference | [docs/api/](docs/api/) |
| Database Schema | [docs/database/](docs/database/) |
| Workflow Engine | [docs/workflows/](docs/workflows/) |
| External Data & APIs | [docs/external-data/](docs/external-data/) |
| AI/ML Guide | [docs/ai/](docs/ai/) |
| Visualization | [docs/visualization/](docs/visualization/) |
| Decisions | [docs/decisions/](docs/decisions/) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## Contributing

We welcome contributions from bioinformaticians, software engineers, data scientists, and researchers.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Quick contribution workflow
git checkout -b feat/my-feature
make lint make typecheck make test
git commit -m "feat(domain): add my feature"
git push origin feat/my-feature
# Open a Pull Request
```

---

## Sponsor

GenomeAI is built and maintained by [Darshan Kachare](https://github.com/dsk-dev-ai) through [NextGenAI Labs](https://github.com/sponsors/dsk-dev-ai).

Sponsorship supports development infrastructure, documentation, and long-term maintenance of this open-source platform.

<a href="https://github.com/sponsors/dsk-dev-ai">
  <img src="https://img.shields.io/badge/%E2%9D%A4%EF%B8%8F-Sponsor_on_GitHub-red?style=for-the-badge&logo=githubsponsors&logoColor=white" alt="Sponsor GenomeAI"/>
</a>

---

## License

GenomeAI is open source under the [Apache 2.0 License](LICENSE).

---

<p align="center">
  Built with care for the global research community.<br/>
  <a href="https://github.com/dsk-dev-ai/GenomeAI">GitHub</a> · <a href="https://github.com/dsk-dev-ai/GenomeAI/discussions">Discussions</a> · <a href="https://github.com/sponsors/dsk-dev-ai">Sponsor</a>
</p>
