# Data Integration Foundation

Reusable backend architecture that lets GenomeAI integrate external scientific
data sources safely and consistently. **18 real external providers are
integrated** on top of this foundation (NCBI, Ensembl VEP, UniProt, ClinVar,
gnomAD, PDB, AlphaFold, ChEMBL, PubChem, Reactome, KEGG, STRING, OpenTargets,
Monarch, Disease Ontology, DGIdb, EuropePMC, Semantic Scholar), plus the
reference connector used as a proof of the architecture.

## What exists today

| Boundary | Module |
| --- | --- |
| Connected external providers (18) | `apps/api/src/genomeai_api/integration/connectors/` |
| Shared vocabulary (source types, access modes, entity types, job states) | `apps/api/src/genomeai_api/integration/types.py` |
| Error hierarchy (structured, credential-free) | `apps/api/src/genomeai_api/integration/errors.py` |
| Connector contract | `apps/api/src/genomeai_api/integration/connectors/base.py` |
| Fetcher (allowlisted HTTP I/O) | `apps/api/src/genomeai_api/integration/connectors/fetcher.py` |
| Reference connector (proof of architecture) | `apps/api/src/genomeai_api/integration/connectors/reference/` |
| Raw-data + provenance records | `apps/api/src/genomeai_api/integration/raw_data.py` |
| Normalization boundary | `apps/api/src/genomeai_api/integration/normalizers/base.py` |
| External identifiers | `apps/api/src/genomeai_api/integration/identifiers.py` |
| Ingestion-job state machine | `apps/api/src/genomeai_api/integration/jobs.py` |
| Source registry | `apps/api/src/genomeai_api/integration/registry.py` |
| Database tables | `apps/api/src/genomeai_api/integration/models/` |
| Admin API | `apps/api/src/genomeai_api/routes/integrations.py` |
| Configuration | `packages/config` → `IntegrationSettings` |

Detailed documents:

- [architecture.md](architecture.md) — pipeline, layers, database schema
- [connectors.md](connectors.md) — connector contract and how to add one
- [provenance.md](provenance.md) — raw records, checksums, identifier mapping
- The 18 implemented providers are listed in
  [connectors.md](connectors.md#implemented-providers)

## Not included yet

- No scheduled synchronization or workflow workers (Celery/Arq)
- No object-storage pipeline or bulk download engine
- No public end-user endpoints for raw external sources (higher-level analysis
  endpoints surface the integrated data instead)
- No AI/vector/RAG ingestion layer

These belong to later milestones and must build on this foundation.

## Quick tour

```python
from genomeai_api.integration.connectors.fetcher import HttpFetcher, FetchRequest
from genomeai_api.integration.services_bootstrap import build_default_registry

registry = build_default_registry()
fetcher = HttpFetcher(
    "https://reference.internal",
    allowed_source_urls=settings.integration.allowed_source_urls,
)
health = await registry.build_connector("genomeai-reference", config, fetcher=fetcher).health_check()
```

## Configuration

`IntegrationSettings` (env prefix `GENOMEAI_INTEGRATION_`):

| Setting | Default | Purpose |
| --- | --- | --- |
| `ALLOWED_SOURCE_URLS` | `[]` | SSRF allowlist; empty means no outbound fetches |
| `REQUEST_TIMEOUT_SECONDS` | `30.0` | Per-request timeout |
| `DEFAULT_MAX_RETRIES` | `0` | Opt-in bounded retries only |
| `ENABLE_INTEGRATION_ROUTES` | `true` | Mounts `/integration/*` admin API |

## Security model in one paragraph

Outbound fetch targets must match the configured allowlist (`http`/`https`
only); user-supplied URLs are never fetch targets. Credentials exist only as
*references* (e.g. `credential_ref` naming an environment variable); they are
never stored, serialized, logged, or attached to requests by this layer.
Errors are structured and carry status codes and retryability flags — not raw
payloads or headers.

## Testing

```bash
uv run pytest apps/api/tests/test_integration_types.py \
              apps/api/tests/test_integration_errors.py \
              apps/api/tests/test_integration_fetcher.py \
              apps/api/tests/test_integration_connector.py \
              apps/api/tests/test_integration_jobs.py \
              apps/api/tests/test_integration_registry.py \
              apps/api/tests/test_integration_raw_data.py \
              apps/api/tests/test_integration_normalization.py \
              apps/api/tests/test_integration_identifiers.py \
              apps/api/tests/test_integration_schemas.py \
              apps/api/tests/test_integration_api.py \
              apps/api/tests/test_integration_migration.py \
              apps/api/tests/test_integration_security.py
```
