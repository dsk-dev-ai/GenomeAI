# GenomeAI Roadmap

Open-source AI platform for genomics, bioinformatics, and biomedical research.

**Design principle:** Build on free public APIs, use local-first AI (Ollama), and deliver quality output with minimal cost. Every integration must be open-source and accessible to researchers worldwide.

---

## Legend

- 📋 Planned
- 🚧 In Progress
- ✅ Released

---

## Delivered Work

| Phase | Milestone | Status | PRs |
|-------|-----------|--------|-----|
| 0 | Repository foundation, docs, governance, CI/CD | ✅ | #1–#6 |
| 1 | Biological domain models (Genome, Sample, Gene, Variant, Transcript) | ✅ | #7–#22 |
| 1 | REST API v1 (CRUD endpoints, schemas, validation) | ✅ | #7–#22 |
| 6 | Visualization platform (genome browser, protein viewer, network graphs, charts) | ✅ | #28–#40 |
| 7 | Data integration foundation (sources, fetchers, connectors) | ✅ | #41 |
| 7.1 | Workflow DAG engine (definitions, steps, dependencies, validation) | ✅ | #42 |
| 7.2 | Deterministic sequential execution engine | ✅ | #43 |
| 7.3 | Cron-based workflow scheduler | ✅ | #44 |
| 7.4 | Queue & worker (Redis-backed background execution) | ✅ | #45 |
| 7.5 | Retry & failure handling (classification, backoff, policies) | ✅ | #46 |
| 7.6 | Parallel DAG execution (concurrent independent steps) | ✅ | #47 |

---

## Phase 4 — Biological Domain Expansion

**Goal:** Complete the core biological data model and connect to public reference databases.

### 4.1 Remaining Domains

| Domain | ORM | Migration | Repo | Service | API | Tests | Status |
|--------|-----|-----------|------|---------|-----|-------|--------|
| Protein | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🚧 |
| Experiment | | | | | | | 📋 |
| Dataset | | | | | | | 📋 |
| Study | | | | | | | 📋 |
| Project | | | | | | | 📋 |

### 4.2 Public Database Connectors

All free, no API key required (API key optional for higher rate limits):

| Connector | Source | Data | API | Rate Limit |
|-----------|--------|------|-----|------------|
| **NCBI E-utilities** | ncbi.nlm.nih.gov | Genes, sequences, literature, variants, proteins | REST (XML/JSON) | 3 req/s (10 with key) |
| **Ensembl REST** | rest.ensembl.org | Gene annotation, transcripts, variants, sequences | REST (JSON) | 55K req/hr |
| **UniProt** | rest.uniprot.org | Protein sequences, annotations, domains | REST (JSON) | 303M req/mo |
| **ClinVar** | via NCBI E-utilities | Clinical variant interpretations | E-utilities | 3 req/s |
| **gnomAD** | gnomad.broadinstitute.org | Population variant frequencies (730K+ individuals) | GraphQL | Generous |
| **PubChem** | pubchem.ncbi.nlm.nih.gov | 110M+ compounds, structures, bioassays | REST (JSON) | 5 req/sec |
| **ChEMBL** | ebi.ac.uk/chembl | 2.9M compounds, 24.5M bioactivity measurements | REST (JSON) | Generous |
| **PubMed** | pubchem.ncbi.nlm.nih.gov | 37M+ biomedical literature citations | E-utilities | 3 req/s |
| **Europe PMC** | ebi.ac.uk/europepmc | Full-text open access articles | REST (JSON) | Generous |
| **RCSB PDB** | rcsb.org | 200K+ experimental protein structures | REST (JSON) | CC0 license |
| **AlphaFold DB** |alphafold.ebi.ac.uk | 241M predicted protein structures | REST | CC-BY-4.0 |
| **Reactome** | reactome.org | Biological pathways | REST (JSON) | Generous |
| **STRING** | string-db.org | Protein-protein interaction networks | REST (TSV/JSON) | Generous |
| **GTEx** |gtexportal.org | Tissue gene expression, eQTLs | REST (v2) | Generous |
| **Open Targets** | api.platform.opentargets.org | Target-disease-variant associations | GraphQL | Generous |
| **ClinicalTrials.gov** | clinicaltrials.gov/api | 500K+ clinical studies | REST (JSON) | Generous |
| **Disease Ontology** | github.com/DiseaseOntology | Standardized disease terms | Download/REST | Open |
| **HPO** | hpo.jax.org | Human phenotype ontology | Download/REST | Open |
| **KEGG** | kegg.jp | Pathway, disease, drug, module data | REST | 1 req/3s (free) |
| **DrugBank** | drugbank.com | Drug-target data (free academic) | XML/REST | Registration |

See [docs/external-data/MASTER_PLAN.md](docs/external-data/MASTER_PLAN.md) for the complete integration architecture.

---

## Phase 5 — Search & Query Engine

**Goal:** Search and query across all biological domains with full-text, faceted, and advanced filtering.

| Feature | Technology | Status |
|---------|-----------|--------|
| Full-text search | PostgreSQL full-text | 📋 |
| Faceted search | PostgreSQL + custom | 📋 |
| Gene/protein/variant search | Domain repositories | 📋 |
| Search suggestions | Elasticsearch/OpenSearch (later) | 📋 |
| Query DSL | Custom query language | 📋 |

---

## Phase 6 — Visualization Platform

**Goal:** Interactive visualization for genomic data, protein structures, and research results.

| Component | Technology | Status |
|-----------|-----------|--------|
| Genome browser | React, Canvas, D3.js | ✅ |
| Protein structure viewer | Mol*, Three.js | ✅ |
| Variant track viewer | React, D3.js | ✅ |
| Network graphs (gene/drug/disease) | Cytoscape.js | ✅ |
| Scientific charts (expression, coverage) | D3.js | ✅ |
| 3D molecular structures | Three.js, Mol* | ✅ |
| Research workspace | React | ✅ |

---

## Phase 7 — Workflow Engine

**Goal:** Execute analysis pipelines with scheduling, retry, and parallel execution.

| Feature | Status |
|---------|--------|
| DAG-based workflow definitions | ✅ |
| Deterministic sequential execution | ✅ |
| Cron-based scheduling | ✅ |
| Redis queue worker | ✅ |
| Retry with failure classification | ✅ |
| Parallel concurrent execution | ✅ |
| Containerized step execution (OCI) | 📋 |
| Kubernetes multi-node execution | 📋 |
| Partial re-execution (resume from failure) | 📋 |

---

## Phase 8 — AI Platform

**Goal:** Multi-provider LLM integration for genomic analysis, literature review, and report generation.

### AI Strategy (Cost-Effective)

| Stage | Provider | Cost | Use Case |
|-------|----------|------|----------|
| **Stage 1 (Default)** | Ollama (local) | Free | All analysis, coding, private data |
| **Stage 1 (Fast)** | Groq free tier | Free | 30 RPM, 500K tokens/day |
| **Stage 1 (Extended)** | Cerebras free tier | Free | 1M tokens/day |
| **Stage 2 (Paid)** | Together AI | $0.05/1M tokens | Large model tasks |
| **Stage 2 (Quality)** | Claude / GPT-5.5 | $3–15/1M tokens | Complex reasoning, review |

### Recommended Local Models

| Model | Size | Use Case |
|-------|------|----------|
| Qwen3 Coder | 8B–32B | Primary coding assistant |
| Qwen2.5 Coder | 7B–32B | Code generation, analysis |
| DeepSeek Coder | 6.7B–33B | Code reasoning |
| Llama 3.1 | 8B–70B | General analysis |
| Gemma 3 | 4B–27B | Research tasks |

### AI Agents

| Agent | Purpose |
|-------|---------|
| Research Agent | Literature search, paper summarization, evidence synthesis |
| Genome Agent | Variant interpretation, genomic analysis |
| Protein Agent | Structure analysis, function prediction |
| Drug Agent | Drug-target analysis, interaction prediction |
| Report Agent | Generate research reports, clinical summaries |
| Coding Agent | Generate analysis code, pipeline scripts |

---

## Phase 9 — Scientific Analysis Engine

**Goal:** Run bioinformatics pipelines and produce analysis results.

| Feature | Technology | Status |
|---------|-----------|--------|
| Sequence alignment | minimap2, BWA-MEM2 | 📋 |
| Variant calling | GATK, DeepVariant | 📋 |
| RNA-seq quantification | Salmon, Kallisto | 📋 |
| Protein structure prediction | AlphaFold | 📋 |
| ML-based variant effect | Trained models | 📋 |
| Statistical analysis | scipy, statsmodels | 📋 |
| Report generation | LLM + templates | 📋 |

---

## Phase 10–15 (Future)

| Phase | Focus |
|-------|-------|
| 10 | Plugin Platform (SDK, registry, marketplace) |
| 11 | Authentication & Organizations (JWT, OAuth, RBAC) |
| 12 | Observability (metrics, tracing, audit logs) |
| 13 | Production Infrastructure (Docker, K8s, Helm, CI/CD) |
| 14 | Desktop & HPC (Electron, SLURM, cluster support) |
| 15 | Enterprise (SSO, HIPAA, GDPR, SOC2) |

---

## Cost-Effective Design Principles

1. **Free APIs first** — NCBI, Ensembl, UniProt, PubChem, PubMed, gnomAD, ClinVar, AlphaFold, PDB — all free, no keys needed
2. **Local AI** — Ollama runs LLMs on consumer hardware; zero API costs for analysis
3. **Open-source everything** — PostgreSQL, Redis, FastAPI, React, D3.js, Mol*
4. **Minimal infrastructure** — Single VPS can run the entire platform
5. **Pay only for scale** — When you outgrow free tiers, Together AI at $0.05/1M tokens is the cheapest paid option

---

## Language Roadmap

| Component | Language | Rationale |
|-----------|----------|-----------|
| API | Python | FastAPI, SQLAlchemy ecosystem |
| Business Logic | Python | Bioinformatics tooling |
| Database | SQL | PostgreSQL |
| Web UI | TypeScript | Next.js, React |
| Visualization | TypeScript | D3.js, Three.js, Cytoscape.js |
| CLI | Python | Click/typer |
| SDK (Python) | Python | Primary user SDK |
| SDK (JS/TS) | TypeScript | Web integrations |
| High-perf Rendering | C++ → WebAssembly | Genome browser performance |
| AI Orchestration | Python | LangChain, Ollama integration |
| Workflow | Python | DAG engine, executors |
| Plugins | Python + TypeScript | Dual SDK support |

---

## Track Progress

- [GitHub Issues](https://github.com/dsk-dev-ai/GenomeAI/issues)
- [Milestones](https://github.com/dsk-dev-ai/GenomeAI/milestones)
- [Discussions](https://github.com/dsk-dev-ai/GenomeAI/discussions)
