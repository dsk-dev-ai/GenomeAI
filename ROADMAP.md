# GenomeAI Roadmap

Open-source AI platform for genomics, bioinformatics, and biomedical research.

**Design principle:** Build on free public APIs, use cost-effective AI (Gemini
cloud by default, Ollama local), and deliver quality output with minimal cost.
Every integration must be open-source and accessible to researchers worldwide.

**Status (2026-08-29):** v1.0.0 released with live demo —
[genomeai.vercel.app](https://genomeai.vercel.app).

---

## Legend

- 📋 Planned
- 🚧 In Progress
- ✅ Released

---

## Delivered Work

| Phase | Milestone | PRs |
|-------|-----------|-----|
| 0 | Repository foundation, docs, governance, CI/CD | #1–#6 |
| 1 | Biological domain models (Genome, Sample, Gene, Variant, Transcript, Protein, Experiment, Dataset, Study, Project) | #7–#22 |
| 1 | REST API v1 (CRUD endpoints + 8 enhanced analysis domains) | #7–#22 |
| 6 | Visualization platform (genome browser, protein viewer, network graphs, charts, molecular structure) | #28–#40 |
| 4 | 18 real external-data connectors (NCBI, UniProt, Ensembl VEP, ClinVar, gnomAD, PDB, AlphaFold, ChEMBL, PubChem, Reactome, KEGG, STRING, OpenTargets, Monarch, Disease Ontology, DGIdb, Europe PMC, Semantic Scholar) | #41+ |
| 5 | Search & query engine (full-text, domain search, query DSL) | later |
| 7 | Data integration foundation (sources, fetchers, connectors) | #41 |
| 7.1 | Workflow DAG engine (definitions, steps, dependencies, validation) | #42 |
| 7.2 | Deterministic execution engine | #43 |
| 7.3 | Cron-based workflow scheduler | #44 |
| 7.4 | Queue & worker (Redis-backed background execution) | #45 |
| 7.5 | Retry & failure handling (classification, backoff, policies) | #46 |
| 7.6 | Parallel DAG execution (concurrent independent steps) | #47 |
| 8 | AI analysis services — gene, variant, protein, drug, pathway, disease, literature, multi-domain report (Gemini + Ollama) | later |
| — | Live demo deployment (Vercel frontend + Render backend, release-driven CI/CD) | later |

---

## Phase 4 — Biological Domain Expansion

**Goal:** Complete the core biological data model and connect to public reference databases.

### 4.1 Remaining Domains

| Domain | ORM | Migration | Repo | Service | API | Tests | Status |
|--------|-----|-----------|------|---------|-----|-------|--------|
| Protein | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Experiment | | | | | | | 🚧 |
| Dataset | | | | | | | 🚧 |
| Study | | | | | | | 🚧 |
| Project | | | | | | | 🚧 |

### 4.2 Public Database Connectors

**Released:** 18 connectors are implemented and live under
`apps/api/src/genomeai_api/integration/connectors/`:

| Connector | Source | Data |
|-----------|--------|------|
| **NCBI E-utilities** | ncbi.nlm.nih.gov | Genes, sequences, literature, variants, proteins |
| **Ensembl VEP** | rest.ensembl.org | Variant annotation |
| **UniProt** | rest.uniprot.org | Protein sequences, annotations, domains |
| **ClinVar** | ncbi.nlm.nih.gov/clinvar | Clinical variant interpretations |
| **gnomAD** | gnomad.broadinstitute.org | Population variant frequencies |
| **RCSB PDB** | rcsb.org | Experimental protein structures |
| **AlphaFold DB** | alphafold.ebi.ac.uk | Predicted protein structures |
| **ChEMBL** | ebi.ac.uk/chembl | Compound bioactivity |
| **PubChem** | pubchem.ncbi.nlm.nih.gov | Compounds, structures, bioassays |
| **Reactome** | reactome.org | Biological pathways |
| **KEGG** | kegg.jp | Pathway, disease, drug, module data |
| **STRING** | string-db.org | Protein-protein interaction networks |
| **Open Targets** | platform.opentargets.org | Target-disease-variant associations |
| **Monarch** | monarchinitiative.org | Disease / phenotype associations |
| **Disease Ontology** | disease-ontology.org | Standardized disease terms |
| **DGIdb** | dgidb.org | Drug-gene interactions |
| **Europe PMC** | ebi.ac.uk/europepmc | Full-text open access articles |
| **Semantic Scholar** | semanticscholar.org | Literature search |

**Planned (not yet implemented):** PubMed E-utilities direct, GTEx, ClinicalTrials.gov,
HPO, DrugBank, GWAS Catalog, LOVD, BioGRID, OMIM, OpenFDA, RxNorm, UCSC.

See [docs/external-data/MASTER_PLAN.md](docs/external-data/MASTER_PLAN.md) for the
historical complete integration plan and [docs/data-integration/](docs/data-integration/README.md)
for the live connector architecture.

---

## Phase 5 — Search & Query Engine

**Goal:** Search and query across all biological domains with full-text, faceted, and advanced filtering.

| Feature | Technology | Status |
|---------|-----------|--------|
| Full-text search | PostgreSQL full-text | ✅ |
| Faceted search | PostgreSQL + custom | ✅ |
| Gene/protein/variant search | Domain repositories | ✅ |
| Search suggestions | Elasticsearch/OpenSearch (later) | 📋 |
| Query DSL | Custom query language | ✅ |

See [docs/search/architecture.md](docs/search/architecture.md) for the live search architecture.

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

### Released (v1.0.0)

| Provider | Use | Status |
|----------|-----|--------|
| **Gemini (cloud)** | Default provider, `gemini-3.6-flash` | ✅ |
| **Ollama (local)** | Free local analysis via `?provider=ollama` | ✅ |
| OpenAI / Anthropic / Groq / Mistral | Planned additional providers | 📋 |

### AI Services (all live)

| Service | What it does |
|---------|-------------|
| Gene analysis | `source: ncbi+ollama` — function, summary, variants, diseases, drugs |
| Variant interpretation | ClinVar/gnomAD + LLM interpretation, ACMG-style classification |
| Protein analysis | UniProt/PDB/AlphaFold + function prediction |
| Drug–target analysis | ChEMBL/PubChem/DGIdb/Open Targets + target summaries |
| Pathway analysis | Reactome/KEGG/STRING + pathway summaries |
| Disease analysis | Disease Ontology/Monarch + disease landscape |
| Literature search | Europe PMC/Semantic Scholar + summarization |
| Multi-domain report | Combined gene→protein→variant→drug→disease report |

### Recommended Local Models

| Model | Size | Use Case |
|-------|------|----------|
| Qwen3 Coder | 8B–32B | Primary coding assistant |
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

1. **Free APIs first** — NCBI, Ensembl, UniProt, ClinVar, gnomAD, AlphaFold, PDB — all free
2. **Cost-effective AI** — Gemini cloud by default; Ollama runs local models at zero API cost
3. **Open-source everything** — PostgreSQL, Redis, FastAPI, React, D3.js, Mol*
4. **Minimal infrastructure** — A single free-tier host runs the entire live demo
5. **Pay only for scale** — When you outgrow free tiers, Gemini's pay-as-you-go pace is minimal

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

---

## V1 Plan

Detailed V1 plan with 12 phases, 80+ sub-phases, and branch-based workflow:

| Document | Purpose |
|----------|---------|
| [V1 Plan Overview](docs/v1-plan/README.md) | Master plan, principles, scope |
| [V1 Phases](docs/v1-plan/PHASES.md) | All phases with sub-phases and branch naming |
| [Free APIs Reference](docs/v1-plan/FREE_APIS.md) | 70+ free databases and APIs |
| [Free AI Strategy](docs/v1-plan/FREE_AI_STRATEGY.md) | Multi-provider fallback chain |
| [Branch Strategy](docs/v1-plan/BRANCH_STRATEGY.md) | Branch naming and workflow |
