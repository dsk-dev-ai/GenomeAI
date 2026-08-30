# `apps/api` — REST API

FastAPI application — the GenomeAI backend, live at
<https://genomeai-api.onrender.com>.

**Technology:** FastAPI, Uvicorn, SQLAlchemy, Pydantic, Python 3.12+

**Entry point:** `src/genomeai_api/main.py` — `main()`

## Route modules (24)

- **Health:** `GET /`, `GET /health`, `GET /ready`, `GET /live`
- **Domains (CRUD):** genomes, samples, genes, variants, transcripts, proteins,
  experiments, datasets, studies, projects
- **Enhanced analysis:** `genes_enhanced`, `variants_enhanced`,
  `proteins_enhanced`, `drugs_enhanced`, `pathways_enhanced`,
  `diseases_enhanced`, `literature_enhanced`, `reports_enhanced`
- **Search:** `search`
- **Workflows & scheduling:** `workflows`, `schedules`
- **Integrations admin:** `integrations`, `admin_limits`

## Domain services

Gene, protein, variant, drug, pathway, disease, literature, and multi-domain
report analysis — each combining 18 public-data connectors (NCBI, UniProt,
Ensembl VEP, ClinVar, gnomAD, PDB, AlphaFold, ChEMBL, PubChem, Reactome, KEGG,
STRING, OpenTargets, Monarch, Disease Ontology, DGIdb, Europe PMC, Semantic
Scholar) with AI (Gemini by default, Ollama local).

**Example:**
```bash
curl -X POST https://genomeai-api.onrender.com/api/v1/genes/analyze \
  -H "Content-Type: application/json" -d '{"symbol":"BRCA1"}'
```