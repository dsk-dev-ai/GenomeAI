# GenomeAI External Data & API Master Plan

**Status:** Accepted — official governing reference for Phases 4–9
**Owner:** GenomeAI core
**Scope:** Every external scientific source, API, connector, ingestion path, and storage decision.

---

## 0. The architecture we will build

```
                    PUBLIC SCIENTIFIC SOURCES
                              |
        +---------------------+---------------------+
        |                     |                     |
      NCBI                 Ensembl                UCSC
      UniProt              ClinVar               gnomAD
      GTEx                 ENCODE                Reactome
      STRING               PDB                   AlphaFold
      Open Targets         HPO                   PubChem
      ChEMBL               PubMed                Europe PMC
        |                     |                     |
        +---------------------+---------------------+
                              |
                 GenomeAI CONNECTOR LAYER
                              |
                    INGESTION PIPELINE
                              |
                  VALIDATION + NORMALIZATION
                              |
              +---------------+---------------+
              |                               |
       PostgreSQL                       Object Storage
       metadata/entities                large files
              |                               |
              +---------------+---------------+
                              |
                    SEARCH / INDEX LAYER
                              |
                     GenomeAI API
                              |
              +---------------+---------------+
              |               |               |
             Web            CLI             AI
        Visualization    Python SDK       Agents
```

**Rule:** the frontend must never call external databases directly. External sources → GenomeAI connectors → ingestion → GenomeAI API → Web/AI.

---

## 1. Tier 1 — Core sources

| Source | Main data | API | Bulk | Priority |
|--------|-----------|-----|------|----------|
| NCBI Datasets | genomes, genes, assemblies | yes | yes | Critical |
| NCBI E-utilities | Gene, Protein, PubMed, ClinVar, etc. | yes | — | Critical |
| Ensembl | genes, transcripts, variants | yes | yes | Critical |
| UCSC | genome tracks/regions | yes | yes | Critical |
| GENCODE | gene/transcript annotation | — | yes | Critical |
| UniProt | proteins | yes | yes | Critical |
| ClinVar | clinical variants | yes | yes | Critical |
| gnomAD | population variation | limited | yes | Critical |
| GTEx | expression/eQTL | yes | yes | Critical |
| ENCODE | regulatory genomics | yes | yes | Critical |
| RCSB PDB | structures | yes | yes | Critical |
| AlphaFold DB | predicted structures | yes | yes | Critical |
| Reactome | pathways | yes | yes | Critical |
| STRING | protein networks | yes | yes | Critical |
| HPO | phenotypes | yes | yes | Critical |
| Disease Ontology | diseases | yes | yes | Critical |
| Open Targets | target/disease/variant | GraphQL | yes | Critical |
| PubMed | literature | yes | — | Critical |
| Europe PMC | literature/full text | yes | yes | Critical |
| PubChem | compounds | yes | yes | Critical |
| ChEMBL | drug/target bioactivity | yes | yes | Critical |

Notes:
- NCBI Datasets v2 REST API: default 5 req/s; 10 req/s with an API key.
- Tier 2/3 sources (BioGRID, IntAct, InterPro, Pfam, cBioPortal, COSMIC, PRIDE, Expression Atlas, DrugCentral, BindingDB, PharmGKB, OpenAlex, Crossref, KEGG, OMIM, DrugBank, ICGC, Orphanet, BRENDA, SIDER) come later. Licensing/access must be reviewed — "public" does not mean unrestricted commercial redistribution.

---

## 2. NCBI connector

One NCBI connector, not scattered clients.

```
GenomeAI NCBI Connector
|
+-- Datasets
|   +-- genome
|   +-- gene
|   +-- virus
|   +-- taxonomy
|
+-- E-utilities
|   +-- Gene
|   +-- Protein
|   +-- Nucleotide
|   +-- PubMed
|   +-- PMC
|   +-- ClinVar
|   +-- PubChem
|
+-- Downloads
    +-- assemblies
    +-- annotations
    +-- sequence data
```

Planned interface (do **not** implement until the data-integration phase):

```python
class NCBIConnector:
    async def get_gene(...)
    async def get_genome(...)
    async def get_assembly(...)
    async def search_gene(...)
    async def search_variant(...)
    async def get_clinvar_record(...)
    async def search_pubmed(...)
```

ClinVar is reachable through E-utilities via `esearch`, `esummary`, `elink`, `efetch`.

---

## 3. Ensembl

Major gene/transcript/variant reference.

```
Ensembl
|
+-- Gene
+-- Transcript
+-- Exon
+-- Variant
+-- Region
+-- Sequence
+-- Comparative genomics
+-- Identifier mapping
```

GenomeAI use: Phase 4 validate/augment domains · Phase 5 search/index · Phase 6 genome browser · Phase 9 scientific analysis.

---

## 4. UCSC

Visualization/reference-track source. Do not hammer it.

- Small interactive query → UCSC API.
- Large dataset → UCSC download → GenomeAI ingestion.
- UCSC guidance: ~1 request/sec normal use; stricter limits for some programmatic uses.

---

## 5. Protein data

```
Gene -> Transcript -> Protein -> UniProt (sequence, annotation, domains, identifiers)
                              |-- RCSB PDB (experimental structure)
                              +-- AlphaFold DB (predicted structure)
```

- RCSB APIs: Data, Search, ModelServer, VolumeServer, Sequence Coordinates, Alignment.
- PDB archive + API data are under CC0 dedication (favorable licensing).

---

## 6. Variant data

```
Variant
|
+-- NCBI dbSNP
+-- ClinVar
+-- gnomAD
+-- GWAS Catalog
+-- ClinGen
+-- Open Targets
+-- cBioPortal / cancer sources
```

Enables the GenomeAI variant story: Genome position → Gene → Transcript → Protein consequence → Population frequency → Clinical significance → Disease associations → Research evidence.

---

## 7. Expression

```
Gene -> GTEx (tissue expression, eQTL, sQTL)
     -> ENCODE (regulatory regions, TF binding, chromatin, epigenomics)
```

GTEx exposes a documented v2 OpenAPI service with eQTL/sQTL and related endpoints.

---

## 8. Disease / phenotype

```
Disease
|
+-- Disease Ontology
+-- HPO
+-- Monarch
+-- Open Targets
+-- ClinGen
+-- Orphanet
```

- Disease Ontology: public OpenAPI 3.1 REST service.
- Monarch: knowledge graph with FastAPI interface (entities, associations, semantic similarity).

---

## 9. Pathways / networks

```
Gene / Protein -> Reactome, STRING, BioGRID, IntAct, Gene Ontology
```

Feeds Phase 6 network visualization and Phase 9 analysis. Reactome has a REST Content Service. STRING has an HTTP API for mapping, networks, enrichment; bulk downloads recommended for complete datasets.

---

## 10. Literature

```
LiteratureConnector -> PubMed, PubMed Central, Europe PMC, Crossref, OpenAlex

paper -> metadata -> full text -> chunking -> embeddings -> vector DB -> RAG -> Research Agent
```

Belongs primarily to Phase 8, not Phase 6.

---

## 11. Drug / chemical layer

```
Compound -> PubChem, ChEMBL, BindingDB, DrugCentral, PharmGKB

Drug -> Target -> Gene -> Variant -> Disease
```

Future "Drug Agent" foundation.

---

## 12. What gets stored in PostgreSQL

Do **not** dump entire external databases into PostgreSQL blindly.

Canonical GenomeAI entities: Genome, Assembly, Chromosome, Gene, Transcript, Protein, Variant, Sample, Experiment, Dataset, Study, Project, Disease, Phenotype, Drug, Publication.

Plus **ExternalIdentifier** — identifier federation:

```
GenomeAI Gene
|
+-- internal_id
+-- symbol = TP53
+-- chromosome = 17
+-- start
+-- end
|
+-- ncbi_gene_id
+-- ensembl_gene_id
+-- hgnc_id
+-- gencode_id
```

---

## 13. Provenance

Every imported record must be traceable.

```
Gene
|
+-- source = Ensembl
+-- source_id = ENSG...
+-- source_version
+-- retrieved_at
+-- release
+-- checksum
+-- source_url
```

Required for scientific reproducibility.

---

## 14. Database architecture

```
                    GenomeAI
                       |
          +------------+------------+
          |            |            |
      PostgreSQL    Object Store   Search
          |            |            |
      entities      FASTA/BAM     PostgreSQL FTS
      metadata      VCF/GFF       OpenSearch
      relations     datasets      later
                       |
                    Analytics
```

- **PostgreSQL:** entities, relationships, metadata, users, projects, experiments, searchable structured records.
- **Object storage:** FASTA, FASTQ, BAM, CRAM, VCF, GFF/GTF, PDB, large datasets, model artifacts.
- **Search:** gene symbols, variant IDs, protein names, publications, full-text, faceted search, autocomplete.
- **Vector DB:** later (Phase 8: Qdrant / pgvector / Milvus).

---

## 15. Data ingestion pipeline

```
Connector -> Fetcher -> Raw Artifact -> Parser -> Validator -> Normalizer
-> Identifier Mapper -> Deduplicator -> Database Writer -> Search Indexer
```

Example (Ensembl): download gene annotation → parse GTF/JSON → validate coordinates → map identifiers → Gene/Transcript/Exon → PostgreSQL → search index.

---

## 16. Accuracy / validation

Three distinct layers — do not confuse them:

1. **Software correctness** (every phase): pytest, ruff, pyright, Biome, Turbo, build.
2. **Data correctness** (when ingestion starts): schema validation, coordinate validation, identifier validation, FK validation, duplicate detection, record counts, checksum validation, source release validation.
3. **Scientific correctness** (Phase 9+): known reference datasets, gold-standard results, published benchmarks, cross-source agreement, expected biological relationships.

"All tests passing" does not equal "GenomeAI's biological data is scientifically accurate."

---

## 17. When do we actually connect APIs (roadmap)

- **Phase 4 — Biological Domains** (near-term): NCBI, Ensembl, GENCODE, HGNC. Establish canonical biological identifiers and relationships.
- **Phase 5 — Search** (largely complete): full text, domain APIs, advanced query, suggestions, coordinates, DSL, backend abstraction. Next: external-source-aware search — but do not turn Phase 5 into a giant ingestion project.
- **Phase 6 — Visualization** (CURRENT):
  - 6.1 Foundation · 6.2 Genome Browser · 6.3 Gene/Transcript Viewer — done.
  - **6.4 Variant Viewer (next)** → use the GenomeAI API backed by ClinVar / gnomAD / dbSNP / Ensembl, never direct browser → external API.
  - 6.5 Protein Viewer → UniProt, RCSB PDB, AlphaFold DB.
  - 6.6 Biological Network Viewer → STRING, Reactome, Gene Ontology, BioGRID.
  - 6.7 Expression Visualization → GTEx, ENCODE.
  - 6.8 Publication/Evidence Visualization → PubMed, Europe PMC, OpenAlex.
  - 6.9 Visualization integration + quality.
- **Phase 7 — Workflow Engine**: serious ingestion begins. Connector, scheduler, queue, worker, retry, cache, checkpoint, dataset version. Example: nightly Ensembl sync → worker → download → validate → normalize → PostgreSQL → search index.
- **Phase 8 — AI Platform**: AI Gateway + Provider Interface (OpenAI, Anthropic, Gemini, OpenRouter, Groq, Together, NVIDIA, Ollama, vLLM, LM Studio); Model/Embedding/Prompt/Tool/Agent registries. Hugging Face Hub is an ecosystem/registry layer, not hard-wired models.
- **Phase 9 — Scientific Analysis**: sequence alignment, variant calling, genome annotation, protein prediction, structure prediction, variant effect prediction, population genetics, statistical analysis. C++ only where a real performance bottleneck demands it (Python → benchmark → Rust/C++ → Python binding).
- **Phase 10 — Plugin ecosystem**: external integrations become plugins (NCBI, Ensembl, UniProt, ClinVar, PDB, Reactome, STRING, PubMed, NVIDIA, custom institutional sources).

---

## 18. API classification

Every external source is classified as one of:

- **A. Live query** — user request → GenomeAI → external API → response. For small metadata, current information, interactive lookup.
- **B. Cached API** — external API only on cache miss. For repeated lookups, expensive APIs, rate-limited sources.
- **C. Ingested dataset** — scheduled ingestion into GenomeAI DB. For genes, variants, annotations, relationships, large metadata.
- **D. Bulk dataset** — external download → object storage → processing → derived database/index. For FASTA, FASTQ, BAM/CRAM, VCF, large expression datasets, complete PDB/other archives.

---

## 19. Priority order

Locked integration sequence (strategic dependency order, not "connect all at once"):

1. NCBI
2. Ensembl
3. GENCODE
4. HGNC
5. UCSC
6. ClinVar
7. dbSNP
8. gnomAD
9. UniProt
10. RCSB PDB
11. AlphaFold DB
12. GTEx
13. ENCODE
14. HPO
15. Disease Ontology
16. Open Targets
17. Reactome
18. STRING
19. PubMed
20. Europe PMC
21. PubChem
22. ChEMBL
23. Monarch
24. GWAS Catalog
25. cBioPortal
26. BioGRID
27. IntAct
28. Human Protein Atlas
29. specialized databases

---

## 20. DataSource registry

Every external source gets a record:

```
DataSource
+-- name
+-- provider
+-- type
+-- API URL
+-- documentation URL
+-- authentication
+-- rate limit
+-- license
+-- access_mode          (live / cached / ingested / bulk)
+-- current release
+-- last synchronization
+-- sync status
+-- enabled
```

Pipeline: `DataSource → Connector → IngestionJob → RawData → NormalizedEntity → ExternalIdentifier → GenomeAI Entity`.

---

## 21. What we build now

Phase 4 (Biological Domains) near-complete · Phase 5 (Search & Query) done · Phase 6 (Visualization) CURRENT.

Do **not** jump to Phase 7 yet. Sequence:

```
Phase 6.4 Variant Viewer
      |
Phase 6.5 Protein Viewer
      |
Phase 6.6 Biological Network Viewer
      |
Phase 6.7 Expression Viewer
      |
Phase 6.8 Literature / Evidence Viewer
      |
Phase 6.9 Visualization integration + quality
      |
Phase 7 Workflow / ingestion infrastructure
```

Finish the visualization layer first, designed against GenomeAI's own API contracts. Phase 7 is where external databases, ingestion, synchronization, provenance, and accuracy validation are built properly.
