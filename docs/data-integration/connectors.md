# Connectors

A connector wraps **one** external scientific source behind a typed,
provider-agnostic interface. Provider-specific behavior (URLs, payload shapes,
rate-limit quirks) belongs inside connector implementations — never in the
core interface or fetcher.

## The contract

```python
from genomeai_api.integration.connectors.base import (
    ConnectorHealth, DataSourceConfig, DataSourceConnector, DataSourceDefinition,
)

class MyConnector(DataSourceConnector):
    definition = DataSourceDefinition(
        source_id="my-source",            # stable internal ID
        provider="Example Foundation",
        display_name="Example Source",
        source_type=SourceType.GENE,      # vocabulary in integration/types.py
        access_mode=AccessMode.LIVE,
        authentication_mode=AuthMode.NONE,
        license_info={"access": "connector-supplied"},  # data only, no legal claims
    )

    def __init__(self, config: DataSourceConfig, *, fetcher: HttpFetcher) -> None:
        super().__init__(config)          # raises if config.enabled is False
        self._fetcher = fetcher           # allowlisted fetcher injected by the service

    @property
    def current_version(self) -> str | None: ...   # real release or None — never fabricated

    async def health_check(self) -> ConnectorHealth: ...

    async def fetch(self, request: object) -> object:
        if not isinstance(request, MyTypedRequest):
            raise TypeError(...)
```

Rules:

- Requests and responses are **typed** (dataclasses); untyped dicts stop at
  the payload parser.
- All HTTP I/O goes through the injected `HttpFetcher` (allowlisted).
- Pagination is expressed by the connector's own request type (page/page_size
  or cursor) — the interface does not prescribe a scheme.
- Retry policy is configured through `DataSourceConfig.max_retries` /
  settings; connectors do not implement their own retry loops.

## Registration

`integration/services_bootstrap.py` is the single wiring point:

```python
def _my_factory(config: DataSourceConfig, *, fetcher: HttpFetcher | None):
    if fetcher is None:
        raise IntegrationConfigurationError("requires an allowlisted fetcher")
    return MyConnector(config, fetcher=fetcher)

registry.register(MyConnector.definition, _my_factory)
```

A source can be persisted via the admin API **only after** its factory is
registered; `POST /integration/sources` validates that the base URL matches
the SSRF allowlist.

## Reference implementation

`connectors/reference/` implements `genomeai-reference`, a deterministic
metadata-only mock demonstrating every boundary:

- `GET /reference/health` → `{"ok": bool, "message": str, "source_version": str}`
- `GET /reference/records?page=&page_size=` → typed record list
- `ReferenceRecordNormalizer` converts records into canonical entities
- Tests run entirely against `httpx.MockTransport` (no network)

See `test_integration_connector.py` for health/fetch/timeout/error coverage.

## Adding a future provider (e.g. NCBI E-utilities)

1. Create `connectors/ncbi/` with a typed request/response pair and a
   normalizer converging on existing canonical entity types.
2. Register the definition + factory in `services_bootstrap.py`.
3. Add the provider base URL to `GENOMEAI_INTEGRATION_ALLOWED_SOURCE_URLS`.
4. If an API key is required: set `credential_ref` to the *name* of the env
   var holding it (`NCBI_API_KEY`) and read it at request time inside the
   connector. Never hardcode, serialize, or log the value.
5. Ingestion itself remains out of scope until Phase 7 workers exist.
