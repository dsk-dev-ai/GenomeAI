# Data Integration Architecture

## Pipeline

The foundation fixes the direction of dependencies: every external byte flows
one way, through typed boundaries.

```
External Source
    ↓
Connector            connectors/ — provider-specific, strongly typed
    ↓
Fetcher              connectors/fetcher.py — allowlisted HTTP I/O
    ↓
Parser / Validator   connector + normalizer (typed payload checks)
    ↓
Normalizer           normalizers/ → NormalizedEntity (canonical shape)
    ↓
Identifier Mapping   identifiers.py → ExternalIdentifier
    ↓
Internal Entity      future Phase 7: canonical GenomeAI entities
    ↓
PostgreSQL           integration/models/ (registry, ids, provenance, jobs)
    ↓
Search Index         existing Phase 5 infrastructure (unchanged)
    ↓
GenomeAI API         routes/integrations.py (admin only)
```

The web UI never calls external databases directly; it talks to GenomeAI APIs.

## Layers

### Data source registry

`data_sources` is the persisted registry: stable `source_id`, provider,
display name, source type, API base URL, documentation URL, auth mode,
credential *reference* (never a secret), rate-limit metadata, license/access
metadata as connector-supplied data, access mode, source version, last sync,
sync status, enabled flag, and feature flags.

The in-code `SourceRegistry` (`integration/registry.py`) maps source IDs to
connector factories. It holds static definitions and builds bound connectors;
it performs no I/O. The join of both registries happens in the service layer:
a source row can be created **only** when a connector for it exists in code.

### Connector interface

`DataSourceConnector` (ABC) exposes `definition`, `current_version`,
`health_check()`, `fetch(request)`, and `close()`. Provider-specific behavior
lives inside implementations; the interface knows nothing about providers.
Constructing a connector with a disabled config raises immediately.

### Fetcher layer

`HttpFetcher` is the single place network I/O happens:

- GET/POST, query parameters, headers, per-request timeout override
- Fail-closed SSRF allowlist (`validate_allowed_url`, `build_public_url`)
- Structured errors: `FetchTimeoutError`, `FetcherTransportError`,
  `FetcherError(status_code, retryable)`
- Cancellation propagates (`asyncio.CancelledError` re-raised)
- Retries are opt-in and bounded (default 0), limited to 429/500/502/503/504,
  honoring `Retry-After`, capped at 5 s
- Rate-limit headers parsed into `RateLimitMetadata` for future policies

### Raw-data boundary

`RawRecord` preserves source, source record id, source version, retrieval
timestamp, the raw payload (or a `payload_ref` to a future object store), and
a SHA-256 checksum. Minimal by design; extensible later.

### Normalization boundary

A `Normalizer` converts one `RawRecord` into a `NormalizedEntity`
(`entity_type`, `entity_id`, deterministic `fields`). Invalid external data
raises `NormalizationError`. NCBI-Gene and Ensembl-Gene normalizers will both
converge on this same canonical shape.

### External identifiers

`ExternalIdentifier` maps `(source, external_id, entity_type, namespace)` →
`genomeai_entity_id` with optional version and provenance. One table, no
duplicated identifier columns scattered across domain tables.

### Ingestion-job foundation

`IngestionJob` is an explicit state machine:
`pending → running → {succeeded | failed | cancelled}` with timestamps, record
counts, and structured error info. Invalid transitions raise
`InvalidJobTransitionError`. No queues or workers exist yet.

## Database schema

Migration `b3d9f6a1c2e4` (down revision `7cf6d6506732`) creates:

- **data_sources** — registry rows; unique index on `source_id`
- **provenance** — traceability rows; FK to `data_sources.source_id`;
  index on `(source_id, source_record_id)`
- **external_identifiers** — FK to `data_sources.source_id` and
  `provenance.id`; two partial unique indexes enforce uniqueness without the
  Postgres NULL-distinct pitfall:
  - `uq_external_identifier (source_id, external_id, entity_type) WHERE namespace IS NULL`
  - `uq_external_identifier_ns (+ namespace) WHERE namespace IS NOT NULL`
  - lookup index on `(entity_type, genomeai_entity_id)`
- **ingestion_jobs** — FK to `data_sources.source_id`; indexes on
  `(source_id)` and `(source_id, state)`

Existing biological-domain tables were not modified.

## API surface

Admin-only, mounted under `/integration` (can be disabled via
`GENOMEAI_INTEGRATION_ENABLE_INTEGRATION_ROUTES=false`):

```
GET    /integration/connectors                       static connector metadata
GET    /integration/sources                          persisted sources
POST   /integration/sources                          register (requires connector + allowlisted URL)
GET    /integration/sources/{source_id}
PATCH  /integration/sources/{source_id}              enable/disable, metadata updates
GET    /integration/sources/{source_id}/health       runs connector health check
POST   /integration/identifiers                      create mapping
GET    /integration/identifiers?source_id=&…         exact lookup
GET    /integration/entities/{type}/{id}/identifiers all mappings of one internal entity
POST   /integration/jobs                             create pending job
GET    /integration/jobs/{job_id}
POST   /integration/jobs/{job_id}/start|complete|fail|cancel
```

Typed errors map to status codes centrally in `main.py`
(404 unknown source/connector, 409 duplicates/configuration/job-transition,
400 unsafe URL).

## Ingestion workflow

Live services (gene, protein, variant, drug, pathway, disease, literature
analysis) call the connectors directly against the public providers. A future
batch path can: create an `IngestionJob` row → transition to running → iterate
connector pages → wrap each item in a `RawRecord` → persist provenance →
normalize → upsert internal entities + external identifiers → record counts and
finish the job. Everything needed for that path already exists.

## Where feeds meet users

The 18 connectors are surfaced through the enhanced analysis services and
routes:

| Slice | Route module | Sources |
| ----- | ------------ | ------- |
| Gene analysis | `routes/genes_enhanced.py` | NCBI, Ensembl, UniProt |
| Variant interpretation | `routes/variants_enhanced.py` | NCBI, Ensembl VEP, ClinVar, gnomAD |
| Protein analysis | `routes/proteins_enhanced.py` | UniProt, PDB, AlphaFold |
| Literature | `routes/literature_enhanced.py` | Europe PMC, Semantic Scholar |
| Drug–target | `routes/drugs_enhanced.py` | ChEMBL, PubChem, DGIdb, Open Targets |
| Pathway | `routes/pathways_enhanced.py` | Reactome, KEGG, STRING |
| Disease | `routes/diseases_enhanced.py` | Disease Ontology, Monarch, Open Targets |
| Multi-domain report | `routes/reports_enhanced.py` | all of the above |
