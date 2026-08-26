# V1 Phases — Detailed Breakdown

Each phase has sub-phases. Each sub-phase gets its own branch.
Work is step-by-step: complete sub-phase → validate → merge → next.

---

## Branch Naming Convention

```
v1/<phase>/<sub-phase>-<short-description>

Examples:
v1/1.1/protein-domain
v1/1.1/experiment-domain
v1/2.1/ncbi-eutils-core
v1/2.2/ensembl-rest-core
v1/4.1/ai-gateway-core
v1/4.2/ollama-provider
```

---

## Phase V1.1 — Core Domain Models

**Goal:** Complete all biological domain models.
**Branch prefix:** `v1/1.1/`

| # | Branch | Domain | Description | Status |
|---|--------|--------|-------------|--------|
| 1 | `v1/1.1/genome-domain` | Genome, Gene, Variant, Transcript | Already built | ✅ |
| 2 | `v1/1.1/sample-domain` | Sample | Already built | ✅ |
| 3 | `v1/1.1/protein-domain` | Protein | ORM, migration, repo, service, API, tests | 🚧 |
| 4 | `v1/1.1/experiment-domain` | Experiment | Experimental conditions, protocols | 📋 |
| 5 | `v1/1.1/dataset-domain` | Dataset | Data collections, versions | 📋 |
| 6 | `v1/1.1/study-domain` | Study | Research studies, cohorts | 📋 |
| 7 | `v1/1.1/project-domain` | Project | Project management | 📋 |
| 8 | `v1/1.1/drug-domain` | Drug/Compound | From ChEMBL/PubChem | 📋 |
| 9 | `v1/1.1/disease-domain` | Disease | From Disease Ontology, Orphanet | 📋 |
| 10 | `v1/1.1/pathway-domain` | Pathway | From Reactome, KEGG | 📋 |
| 11 | `v1/1.1/literature-domain` | Literature | Publications, citations | 📋 |

Each sub-phase deliverables:
- SQLAlchemy ORM model
- Alembic migration
- Repository (database access)
- Service (business logic)
- Pydantic schemas
- REST API endpoints
- Tests (unit + integration)
- Documentation

---

## Phase V1.2 — Database Connectors

**Goal:** Connect to 50+ free public APIs.
**Branch prefix:** `v1/2.X/`

### V1.2.1 — NCBI Connector
| Branch | Description |
|--------|-------------|
| `v1/2.1/ncbi-eutils-core` | Core E-utilities client (esearch, efetch, esummary, elink) |
| `v1/2.1/ncbi-gene` | Gene search and retrieval |
| `v1/2.1/ncbi-sequence` | Nucleotide/protein sequence retrieval |
| `v1/2.1/ncbi-datasets` | NCBI Datasets API v2 |

### V1.2.2 — Ensembl Connector
| Branch | Description |
|--------|-------------|
| `v1/2.2/ensembl-rest-core` | Core REST client with rate limiting |
| `v1/2.2/ensembl-gene` | Gene annotation, transcripts, exons |
| `v1/2.2/ensembl-variant` | Variant Effect Predictor (VEP) |
| `v1/2.2/ensembl-sequence` | Sequence retrieval and cross-references |

### V1.2.3 — Protein Connectors
| Branch | Description |
|--------|-------------|
| `v1/2.3/uniprot-connector` | UniProt protein sequences and annotations |
| `v1/2.3/pdb-connector` | RCSB PDB experimental structures |
| `v1/2.3/alphafold-connector` | AlphaFold predicted structures |
| `v1/2.3/hpa-connector` | Human Protein Atlas expression data |

### V1.2.4 — Variant Connectors
| Branch | Description |
|--------|-------------|
| `v1/2.4/clinvar-connector` | ClinVar clinical variant interpretations |
| `v1/2.4/gnomad-connector` | gnomAD population frequencies (GraphQL) |
| `v1/2.4/dbsnp-connector` | dbSNP variant identifiers |
| `v1/2.4/gwas-connector` | GWAS Catalog trait associations |
| `v1/2.4/cbioportal-connector` | cBioPortal cancer genomics |

### V1.2.5 — Literature Connectors
| Branch | Description |
|--------|-------------|
| `v1/2.5/pubmed-connector` | PubMed E-utilities search and retrieval |
| `v1/2.5/europepmc-connector` | Europe PMC full-text and text-mining |
| `v1/2.5/semanticscholar-connector` | Semantic Scholar citations and embeddings |
| `v1/2.5/openalex-connector` | OpenAlex scholarly graph |

### V1.2.6 — Drug & Compound Connectors
| Branch | Description |
|--------|-------------|
| `v1/2.6/chembl-connector` | ChEMBL compounds and bioactivity |
| `v1/2.6/pubchem-connector` | PubChem compounds and assays |
| `v1/2.6/dgidb-connector` | DGIdb drug-gene interactions |
| `v1/2.6/pharmgkb-connector` | PharmGKB pharmacogenomics |

### V1.2.7 — Pathway & Network Connectors
| Branch | Description |
|--------|-------------|
| `v1/2.7/reactome-connector` | Reactome pathways |
| `v1/2.7/kegg-connector` | KEGG pathways, modules, diseases |
| `v1/2.7/string-connector` | STRING protein interactions |
| `v1/2.7/biogrid-connector` | BioGRID interactions (free API key) |
| `v1/2.7/wikipathways-connector` | WikiPathways community pathways |

### V1.2.8 — Specialized Connectors
| Branch | Description |
|--------|-------------|
| `v1/2.8/encode-connector` | ENCODE regulatory genomics |
| `v1/2.8/gtex-connector` | GTEx tissue expression and eQTL |
| `v1/2.8/clinicaltrials-connector` | ClinicalTrials.gov |
| `v1/2.8/hp-connector` | Human Phenotype Ontology |
| `v1/2.8/ols-connector` | EBI Ontology Lookup Service |
| `v1/2.8/depmap-connector` | DepMap CRISPR essentiality |
| `v1/2.8/cellxgene-connector` | CZ CELLxGENE single-cell |
| `v1/2.8/ignet-connector` | Ignet literature-mined interactions |

---

## Phase V1.3 — Workflow Engine

**Status:** ✅ DONE (Phases 7.1–7.6, PRs #42–#47)

No additional work needed for V1.

---

## Phase V1.4 — AI Gateway

**Goal:** Multi-provider LLM gateway with intelligent fallback chain.
**Branch prefix:** `v1/4.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/4.1/ai-gateway-core` | Core AI gateway: provider abstraction, unified interface, model registry |
| 2 | `v1/4.2/ollama-provider` | Ollama local provider (unlimited, zero cost) |
| 3 | `v1/4.3/gemini-provider` | Google Gemini free tier (250 req/day) |
| 4 | `v1/4.4/openrouter-provider` | OpenRouter free tier (50-1000 req/day) |
| 5 | `v1/4.5/groq-provider` | Groq free tier (1000-14400 req/day) |
| 6 | `v1/4.6/mistral-provider` | Mistral free tier (~1B tokens/month) |
| 7 | `v1/4.7/fallback-chain` | Intelligent fallback: Ollama → Gemini → OpenRouter → Groq → Mistral |
| 8 | `v1/4.8/rate-limiter` | Client-side rate limiting and quota tracking |
| 9 | `v1/4.9/function-calling` | Tool/function calling support across providers |

---

## Phase V1.5 — Search & Query Engine

**Goal:** Full-text and faceted search across all biological domains.
**Branch prefix:** `v1/5.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/5.1/search-infrastructure` | PostgreSQL full-text search, GIN indexes, search configuration |
| 2 | `v1/5.2/gene-search` | Gene symbol, name, alias search with autocomplete |
| 3 | `v1/5.3/protein-search` | Protein accession, name, function search |
| 4 | `v1/5.4/variant-search` | Variant ID, position, clinical significance search |
| 5 | `v1/5.5/drug-search` | Drug name, target, mechanism search |
| 6 | `v1/5.6/disease-search` | Disease name, ontology term search |
| 7 | `v1/5.7/literature-search` | Publication title, abstract, author search |
| 8 | `v1/5.8/faceted-search` | Faceted filtering across all domains |
| 9 | `v1/5.9/search-api` | Unified search API endpoint |

---

## Phase V1.6 — Visualization Platform

**Status:** ✅ DONE (Phases 6.11–6.12, PRs #28–#40)

No additional work needed for V1.

---

## Phase V1.7 — Data Integration

**Goal:** Ingestion pipelines from public databases into GenomeAI.
**Branch prefix:** `v1/7.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/7.1/ingestion-pipeline` | Core ingestion framework: fetch → validate → normalize → store |
| 2 | `v1/7.2/gene-ingestion` | Gene data ingestion from NCBI + Ensembl |
| 3 | `v1/7.3/variant-ingestion` | Variant data ingestion from ClinVar + gnomAD + dbSNP |
| 4 | `v1/7.4/protein-ingestion` | Protein data ingestion from UniProt + PDB + AlphaFold |
| 5 | `v1/7.5/drug-ingestion` | Drug data ingestion from ChEMBL + PubChem |
| 6 | `v1/7.6/literature-ingestion` | Literature ingestion from PubMed + Europe PMC |
| 7 | `v1/7.7/pathway-ingestion` | Pathway data ingestion from Reactome + KEGG |
| 8 | `v1/7.8/disease-ingestion` | Disease data ingestion from Disease Ontology + Orphanet |
| 9 | `v1/7.9/provenance` | Data provenance tracking and versioning |

---

## Phase V1.8 — Literature Analysis

**Goal:** PubMed search, evidence synthesis, summarization using free AI.
**Branch prefix:** `v1/8.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/8.1/pubmed-search` | Advanced PubMed search with filters, date ranges, MeSH terms |
| 2 | `v1/8.2/fulltext-search` | Europe PMC full-text search |
| 3 | `v1/8.3/citation-network` | Citation network analysis (Semantic Scholar) |
| 4 | `v1/8.4/text-mining` | Gene/disease/chemical mention extraction from abstracts |
| 5 | `v1/8.5/evidence-synthesis` | Combine evidence from multiple papers |
| 6 | `v1/8.6/summarization` | LLM-powered paper summarization (free providers) |
| 7 | `v1/8.7/review-generation` | Generate literature review drafts |

---

## Phase V1.9 — Drug & Compound Analysis

**Goal:** Drug-target analysis, compound lookup, pharmacogenomics.
**Branch prefix:** `v1/9.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/9.1/drug-lookup` | Drug search and detail retrieval (ChEMBL, PubChem) |
| 2 | `v1/9.2/drug-target` | Drug-target interaction analysis |
| 3 | `v1/9.3/drug-gene` | Drug-gene interaction network (DGIdb) |
| 4 | `v1/9.4/compound-search` | Chemical compound search and structure |
| 5 | `v1/9.5/pharmacogenomics` | PharmGKB pharmacogenomic annotations |
| 6 | `v1/9.6/drug-interactions` | Drug-drug interaction prediction |
| 7 | `v1/9.7/drug-report` | Generate drug analysis reports |

---

## Phase V1.10 — Variant Interpretation

**Goal:** ClinVar + gnomAD + AI-assisted pathogenicity assessment.
**Branch prefix:** `v1/10.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/10.1/variant-lookup` | Variant search by position, gene, consequence |
| 2 | `v1/10.2/clinical-significance` | ClinVar clinical significance retrieval |
| 3 | `v1/10.3/population-frequency` | gnomAD allele frequency analysis |
| 4 | `v1/10.4/consequence-prediction` | In-silico prediction (SIFT, PolyPhen via Ensembl VEP) |
| 5 | `v1/10.5/pathogenicity-score` | AI-assisted pathogenicity scoring (ACMG criteria) |
| 6 | `v1/10.6/gene-phenotype` | Gene-phenotype association analysis |
| 7 | `v1/10.7/variant-report` | Generate variant interpretation reports |

---

## Phase V1.11 — Report Generation

**Goal:** LLM-powered research and clinical reports.
**Branch prefix:** `v1/11.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/11.1/report-engine` | Core report generation engine (templates + LLM) |
| 2 | `v1/11.2/variant-report` | Variant interpretation report template |
| 3 | `v1/11.3/drug-report` | Drug analysis report template |
| 4 | `v1/11.4/literature-review` | Literature review report template |
| 5 | `v1/11.5/genomic-summary` | Genomic analysis summary report |
| 6 | `v1/11.6/export` | PDF, HTML, Markdown export |

---

## Phase V1.12 — Testing & Quality

**Goal:** Real database testing, validation, documentation.
**Branch prefix:** `v1/12.X/`

| # | Branch | Description |
|---|--------|-------------|
| 1 | `v1/12.1/connector-tests` | Integration tests for all 50+ connectors |
| 2 | `v1/12.2/ai-tests` | AI gateway tests with all free providers |
| 3 | `v1/12.3/search-tests` | Search and query validation |
| 4 | `v1/12.4/e2e-tests` | End-to-end workflow tests |
| 5 | `v1/12.5/performance` | Performance benchmarks |
| 6 | `v1/12.6/documentation` | Complete API and user documentation |
| 7 | `v1/12.7/validation` | Final validation: all features working with real data |

---

## Delivery Order

```
V1.1 (Core Domains) → V1.2 (Connectors) → V1.4 (AI Gateway) →
V1.5 (Search) → V1.7 (Data Integration) → V1.8 (Literature) →
V1.9 (Drugs) → V1.10 (Variant Interpretation) → V1.11 (Reports) →
V1.12 (Testing & Quality)

V1.3 (Workflow Engine) — already done
V1.6 (Visualization) — already done
```

After V1 fully tested → V2 adds authentication and paid APIs.
