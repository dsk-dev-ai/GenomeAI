from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.search.backends.elasticsearch import ElasticsearchBackend
from genomeai_api.search.backends.opensearch import OpenSearchBackend
from genomeai_api.search.backends.postgres import PostgresBackend
from genomeai_api.search.config import BackendConfig
from genomeai_api.search.interfaces import SearchBackend


def create_backend(
    config: BackendConfig,
    session: AsyncSession | None = None,
) -> SearchBackend:
    if config.is_opensearch:
        return OpenSearchBackend(
            hosts=[config.url] if config.url else None,
            username=config.username,
            password=config.password,
            index_prefix=config.index_prefix,
        )
    if config.is_elasticsearch:
        return ElasticsearchBackend(
            hosts=[config.url] if config.url else None,
            username=config.username,
            password=config.password,
            index_prefix=config.index_prefix,
        )
    if session is None:
        msg = "PostgresBackend requires an AsyncSession"
        raise ValueError(msg)
    return PostgresBackend(session)
