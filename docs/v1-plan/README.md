# GenomeAI V1 Plan

**Goal:** Fully working genomics research platform using ONLY free APIs and free AI. Every feature must work perfectly with zero cost.

**Design principle:** Authentication, paid APIs, and premium features come in V2. V1 is 100% free, fully tested, and production-ready on free tiers.

---

## V1 Principles

1. **Zero cost** — All APIs free, all AI free (Ollama local + free cloud tiers)
2. **Fully tested** — Every connector, every AI feature, every workflow tested against real databases
3. **Quality output** — Results must be useful for real medical researchers
4. **Branch-based** — Each phase and sub-phase gets its own branch
5. **Step-by-step** — Complete one sub-phase, validate, merge, then move to next
6. **No paid anything** — No credit cards, no subscriptions, no paid APIs in V1

---

## V1 Scope

### What V1 INCLUDES

- Core biological domain models (Genome, Sample, Gene, Variant, Transcript, Protein, etc.)
- 50+ free public database connectors (NCBI, Ensembl, UniProt, ClinVar, gnomAD, PubMed, ChEMBL, PubChem, PDB, AlphaFold, etc.)
- Multi-provider AI gateway (Ollama local → Google Gemini free → OpenRouter free → Groq free)
- DAG-based workflow engine with parallel execution, retry, scheduling
- Full-text and faceted search across all biological domains
- Genome browser, protein viewer, network graphs, scientific charts
- Literature search and analysis
- Drug-target and compound analysis
- Variant interpretation with AI assistance
- Research report generation
- All tested against real databases with real data

### What V1 EXCLUDES (V2+)

- Authentication and authorization (JWT, OAuth, ABAC)
- Paid AI APIs (OpenAI, Claude, etc.)
- Paid database APIs (DrugBank commercial, HGMD, etc.)
- Kubernetes multi-node execution
- Plugin marketplace
- Enterprise features (SSO, HIPAA, GDPR)
- Desktop/HPC integration

---

## V1 Phases Overview

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| V1.1 | Core Domain Models | Complete biological domain models | 🚧 Partially done |
| V1.2 | Database Connectors | Connect to 50+ free public APIs | 📋 |
| V1.3 | Workflow Engine | DAG execution, scheduling, retry, parallel | ✅ Done (7.1-7.6) |
| V1.4 | AI Gateway | Multi-provider LLM with free fallback chain | 📋 |
| V1.5 | Search & Query | Full-text, faceted, gene/protein/variant search | 📋 |
| V1.6 | Visualization | Genome browser, protein viewer, charts | ✅ Done (28-40) |
| V1.7 | Data Integration | Ingestion pipelines from public databases | 📋 |
| V1.8 | Literature Analysis | PubMed search, evidence synthesis, summarization | 📋 |
| V1.9 | Drug & Compound | Drug-target analysis, compound lookup | 📋 |
| V1.10 | Variant Interpretation | ClinVar + gnomAD + AI-assisted pathogenicity | 📋 |
| V1.11 | Report Generation | LLM-powered research and clinical reports | 📋 |
| V1.12 | Testing & Quality | Real database testing, validation, documentation | 📋 |

---

## Documents

| Document | Purpose |
|----------|---------|
| [PHASES.md](PHASES.md) | All phases with sub-phases and branch naming |
| [FREE_APIS.md](FREE_APIS.md) | Complete free API and database reference |
| [FREE_AI_STRATEGY.md](FREE_AI_STRATEGY.md) | AI provider fallback strategy |
| [BRANCH_STRATEGY.md](BRANCH_STRATEGY.md) | Branch naming and workflow |

---

## V1 Delivery Order

```
V1.1 (Core Domains) → V1.2 (Connectors) → V1.4 (AI Gateway) →
V1.5 (Search) → V1.7 (Data Integration) → V1.8 (Literature) →
V1.9 (Drugs) → V1.10 (Variant Interpretation) → V1.11 (Reports) →
V1.12 (Testing & Quality)

V1.3 (Workflow Engine) — already done
V1.6 (Visualization) — already done
```

After V1 is fully tested and working → V2 adds authentication and paid APIs.
