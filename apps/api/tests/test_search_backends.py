from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from genomeai_api.models.study import Study
from genomeai_api.repositories.search import SearchResult
from genomeai_api.schemas.search import (
    FullTextSearchConfig,
    PaginationRequest,
    SearchRequest,
)
from genomeai_api.search.backends.elasticsearch import ElasticsearchBackend
from genomeai_api.search.backends.factory import create_backend
from genomeai_api.search.backends.opensearch import OpenSearchBackend
from genomeai_api.search.backends.postgres import PostgresBackend
from genomeai_api.search.config import BackendConfig
from genomeai_api.search.index_management import (
    INDEX_MAPPINGS,
    SUPPORTED_INDEX_TYPES,
    create_index,
    delete_index,
    index_exists,
)
from genomeai_api.search.interfaces import SearchBackend
from genomeai_api.services.search import SearchService


class TestBackendConfig:
    def test_default_is_postgres(self) -> None:
        config = BackendConfig()
        assert config.backend == "postgres"
        assert config.is_postgres is True
        assert config.is_opensearch is False
        assert config.is_elasticsearch is False

    def test_opensearch_config(self) -> None:
        config = BackendConfig(backend="opensearch")
        assert config.is_opensearch is True

    def test_elasticsearch_config(self) -> None:
        config = BackendConfig(backend="elasticsearch")
        assert config.is_elasticsearch is True

    def test_custom_url(self) -> None:
        config = BackendConfig(
            backend="opensearch",
            url="https://myhost:9200",
            username="admin",
            password="pass",
            index_prefix="myapp",
        )
        assert config.url == "https://myhost:9200"
        assert config.username == "admin"
        assert config.password == "pass"
        assert config.index_prefix == "myapp"


class TestSearchBackendInterface:
    def test_all_backends_implement_interface(self) -> None:
        assert issubclass(PostgresBackend, SearchBackend)
        assert issubclass(OpenSearchBackend, SearchBackend)
        assert issubclass(ElasticsearchBackend, SearchBackend)


class TestPostgresBackend:
    @pytest.mark.asyncio
    async def test_search_delegates_to_repository(self) -> None:
        session = MagicMock()

        backend = PostgresBackend(session)
        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))

        with patch(
            "genomeai_api.search.backends.postgres._execute_search",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = SearchResult(
                items=["a", "b"],
                total_count=2,
                page=1,
                page_size=10,
            )
            result = await backend.search(Study, request)
            assert isinstance(result, SearchResult)
            assert result.total_count == 2
            assert result.items == ["a", "b"]

    @pytest.mark.asyncio
    async def test_search_fts_delegates(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        rank_scalar = MagicMock()
        rank_scalar.all.return_value = [0.5]
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        backend = PostgresBackend(session)
        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))
        fts_config = FullTextSearchConfig(
            columns=["study_name"],
            query="cancer",
        )
        # Just verify it doesn't crash and returns an FTSResult
        with patch(
            "genomeai_api.search.backends.postgres._execute_fts_search",
            new_callable=AsyncMock,
        ) as mock_fts:
            mock_fts.return_value = MagicMock(
                items=["item"],
                total_count=1,
                page=1,
                page_size=10,
                total_pages=1,
                has_next=False,
                has_previous=False,
                ranks=[0.5],
                highlights=None,
            )
            await backend.search_fts(request=request, model=Study, fts_config=fts_config)
            mock_fts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_suggest_delegates(self) -> None:
        session = AsyncMock(spec=["execute"])

        backend = PostgresBackend(session)
        with patch(
            "genomeai_api.search.backends.postgres._execute_suggestions",
            new_callable=AsyncMock,
        ) as mock_suggest:
            mock_suggest.return_value = ["alpha", "beta"]
            result = await backend.suggest(Study, "study_name", "al", 5)
            assert result == ["alpha", "beta"]
            mock_suggest.assert_awaited_once_with(session, Study, "study_name", "al", 5)

    @pytest.mark.asyncio
    async def test_health_check_returns_true(self) -> None:
        session = AsyncMock(spec=["execute"])
        scalar = MagicMock()
        scalar.scalar_one.return_value = 1
        session.execute = AsyncMock(return_value=scalar)

        backend = PostgresBackend(session)
        healthy = await backend.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_health_check_with_mocked_session(self) -> None:
        session = AsyncMock(spec=["execute"])
        session.execute = AsyncMock(side_effect=Exception("db down"))

        backend = PostgresBackend(session)
        healthy = await backend.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_search_dsl_delegates_to_repository(self) -> None:
        session = AsyncMock(spec=["execute"])
        backend = PostgresBackend(session)
        from genomeai_api.schemas.search import PaginationRequest
        from genomeai_api.search.dsl_types import DslSearchQuery

        request = DslSearchQuery(
            where={"field": "id", "op": "eq", "value": 1},
            pagination=PaginationRequest(page=1, page_size=10),
        )
        with patch(
            "genomeai_api.search.backends.postgres._execute_dsl_search",
            new_callable=AsyncMock,
        ) as mock_dsl:
            mock_dsl.return_value = SearchResult(
                items=["result"], total_count=1, page=1, page_size=10,
            )
            result = await backend.search_dsl(Study, request)
            assert result.total_count == 1
            mock_dsl.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_index_operations_raise_not_implemented(self) -> None:
        backend = PostgresBackend(AsyncMock())
        with pytest.raises(NotImplementedError):
            await backend.index_document("study", "1", {})
        with pytest.raises(NotImplementedError):
            await backend.update_document("study", "1", {})
        with pytest.raises(NotImplementedError):
            await backend.delete_document("study", "1")
        with pytest.raises(NotImplementedError):
            await backend.bulk_index("study", [{}])


class TestOpenSearchBackend:
    @pytest.mark.asyncio
    async def test_health_check_without_client_returns_false(self) -> None:
        backend = OpenSearchBackend()
        healthy = await backend.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_health_check_with_mocked_client(self) -> None:
        backend = OpenSearchBackend()
        mock_client = MagicMock()
        mock_client.info.return_value = {"status": 200, "cluster_name": "test"}
        backend._client = mock_client
        healthy = await backend.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_index_document(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await backend.index_document("study", "doc123", {"name": "Test"})
        mock_client.index.assert_called_once_with(
            index="test_study", id="doc123", body={"name": "Test"}
        )

    @pytest.mark.asyncio
    async def test_update_document(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await backend.update_document("study", "doc123", {"name": "Updated"})
        mock_client.update.assert_called_once_with(
            index="test_study", id="doc123", body={"doc": {"name": "Updated"}}
        )

    @pytest.mark.asyncio
    async def test_delete_document(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await backend.delete_document("study", "doc123")
        mock_client.delete.assert_called_once_with(index="test_study", id="doc123")

    @pytest.mark.asyncio
    async def test_bulk_index(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        docs = [
            {"_id": "1", "name": "A"},
            {"_id": "2", "name": "B"},
        ]
        await backend.bulk_index("study", docs)
        mock_client.bulk.assert_called_once()
        body = mock_client.bulk.call_args[1]["body"]
        assert len(body) == 4  # 2 actions + 2 docs
        assert body[0]["index"]["_index"] == "test_study"
        assert body[0]["index"]["_id"] == "1"

    @pytest.mark.asyncio
    async def test_bulk_index_does_not_mutate_docs(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        backend._client = MagicMock()
        docs = [{"_id": "1", "name": "A"}]
        original = list(docs)
        await backend.bulk_index("study", docs)
        assert docs == original  # caller's list unchanged
        assert "_id" in docs[0]  # original doc not mutated

    @pytest.mark.asyncio
    async def test_search_not_implemented(self) -> None:
        backend = OpenSearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.search(object, object)

    @pytest.mark.asyncio
    async def test_search_fts_not_implemented(self) -> None:
        backend = OpenSearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.search_fts(object, object, object)

    @pytest.mark.asyncio
    async def test_suggest_not_implemented(self) -> None:
        backend = OpenSearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.suggest(object, "col", "q")

    @pytest.mark.asyncio
    async def test_coordinate_search_not_implemented(self) -> None:
        backend = OpenSearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.coordinate_search(object, object)

    @pytest.mark.asyncio
    async def test_search_dsl_not_implemented(self) -> None:
        backend = OpenSearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.search_dsl(object, object)


class TestElasticsearchBackend:
    @pytest.mark.asyncio
    async def test_health_check_without_client_returns_false(self) -> None:
        backend = ElasticsearchBackend()
        healthy = await backend.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_health_check_with_mocked_client(self) -> None:
        backend = ElasticsearchBackend()
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        backend._client = mock_client
        healthy = await backend.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_index_document(self) -> None:
        backend = ElasticsearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await backend.index_document("study", "doc123", {"name": "Test"})
        mock_client.index.assert_called_once_with(
            index="test_study", id="doc123", body={"name": "Test"}
        )

    @pytest.mark.asyncio
    async def test_update_document(self) -> None:
        backend = ElasticsearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await backend.update_document("study", "doc123", {"name": "Updated"})
        mock_client.update.assert_called_once_with(
            index="test_study", id="doc123", body={"doc": {"name": "Updated"}}
        )

    @pytest.mark.asyncio
    async def test_delete_document(self) -> None:
        backend = ElasticsearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await backend.delete_document("study", "doc123")
        mock_client.delete.assert_called_once_with(index="test_study", id="doc123")

    @pytest.mark.asyncio
    async def test_bulk_index(self) -> None:
        backend = ElasticsearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        docs = [{"_id": "1", "name": "A"}, {"_id": "2", "name": "B"}]
        await backend.bulk_index("study", docs)
        mock_client.bulk.assert_called_once()
        body = mock_client.bulk.call_args[1]["body"]
        assert len(body) == 4

    @pytest.mark.asyncio
    async def test_bulk_index_does_not_mutate_docs(self) -> None:
        backend = ElasticsearchBackend(index_prefix="test")
        backend._client = MagicMock()
        docs = [{"_id": "1", "name": "A"}]
        original = list(docs)
        await backend.bulk_index("study", docs)
        assert docs == original
        assert "_id" in docs[0]

    @pytest.mark.asyncio
    async def test_search_not_implemented(self) -> None:
        backend = ElasticsearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.search(object, object)

    @pytest.mark.asyncio
    async def test_search_fts_not_implemented(self) -> None:
        backend = ElasticsearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.search_fts(object, object, object)

    @pytest.mark.asyncio
    async def test_search_dsl_not_implemented(self) -> None:
        backend = ElasticsearchBackend()
        with pytest.raises(NotImplementedError):
            await backend.search_dsl(object, object)


class TestBackendFactory:
    def test_create_postgres_with_session(self) -> None:
        session = AsyncMock()
        backend = create_backend(BackendConfig(backend="postgres"), session)
        assert isinstance(backend, PostgresBackend)

    def test_create_postgres_without_session_raises(self) -> None:
        with pytest.raises(ValueError, match="requires an AsyncSession"):
            create_backend(BackendConfig(backend="postgres"))

    def test_create_opensearch(self) -> None:
        config = BackendConfig(
            backend="opensearch",
            url="https://os:9200",
            username="admin",
            password="pass",
            index_prefix="myapp",
        )
        backend = create_backend(config)
        assert isinstance(backend, OpenSearchBackend)
        assert backend._hosts == ["https://os:9200"]
        assert backend._username == "admin"
        assert backend._password == "pass"
        assert backend._index_prefix == "myapp"

    def test_create_elasticsearch(self) -> None:
        config = BackendConfig(
            backend="elasticsearch",
            index_prefix="myapp",
        )
        backend = create_backend(config)
        assert isinstance(backend, ElasticsearchBackend)
        assert backend._index_prefix == "myapp"

    def test_unknown_backend_raises(self) -> None:
        config = BackendConfig(backend="unknown")
        with pytest.raises(ValueError, match="Unknown backend.*unknown"):
            create_backend(config)

    def test_unknown_backend_raises_even_with_session(self) -> None:
        config = BackendConfig(backend="unknown")
        with pytest.raises(ValueError, match="Unknown backend.*unknown"):
            create_backend(config, session=AsyncMock())


class TestIndexManagement:
    @pytest.mark.asyncio
    async def test_create_index(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await create_index(backend, "study")
        mock_client.indices.create.assert_called_once()
        assert mock_client.indices.create.call_args[1]["index"] == "test_study"

    @pytest.mark.asyncio
    async def test_create_index_uses_per_type_mappings(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await create_index(backend, "gene")
        body = mock_client.indices.create.call_args[1]["body"]
        assert body["mappings"] == INDEX_MAPPINGS["gene"]

    @pytest.mark.asyncio
    async def test_create_index_with_custom_mappings(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        custom = {"properties": {"custom_field": {"type": "text"}}}
        await create_index(backend, "study", custom)
        body = mock_client.indices.create.call_args[1]["body"]
        assert body["mappings"] == custom

    @pytest.mark.asyncio
    async def test_create_index_unsupported_type(self) -> None:
        backend = OpenSearchBackend()
        with pytest.raises(ValueError, match="Unsupported index type"):
            await create_index(backend, "unsupported_type")

    @pytest.mark.asyncio
    async def test_create_index_on_postgres_raises(self) -> None:
        backend = PostgresBackend(AsyncMock())
        with pytest.raises(NotImplementedError):
            await create_index(backend, "study")

    @pytest.mark.asyncio
    async def test_delete_index(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        backend._client = mock_client
        await delete_index(backend, "study")
        mock_client.indices.delete.assert_called_once_with(
            index="test_study", ignore_unavailable=True
        )

    @pytest.mark.asyncio
    async def test_index_exists(self) -> None:
        backend = OpenSearchBackend(index_prefix="test")
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = True
        backend._client = mock_client
        result = await index_exists(backend, "study")
        assert result is True
        mock_client.indices.exists.assert_called_once_with(index="test_study")

    def test_supported_index_types(self) -> None:
        assert "study" in SUPPORTED_INDEX_TYPES
        assert "gene" in SUPPORTED_INDEX_TYPES
        assert "variant" in SUPPORTED_INDEX_TYPES
        assert len(SUPPORTED_INDEX_TYPES) == 10

    def test_all_index_types_have_mappings(self) -> None:
        for t in SUPPORTED_INDEX_TYPES:
            assert t in INDEX_MAPPINGS
            assert "properties" in INDEX_MAPPINGS[t]


class TestSearchServiceWithBackend:
    @pytest.mark.asyncio
    async def test_service_uses_postgres_backend_by_default(self) -> None:
        session = AsyncMock(spec=["execute"])

        scalar = MagicMock()
        scalar.scalar_one.return_value = 1

        mock_scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=["item"]))
        )
        session.execute = AsyncMock(return_value=MagicMock(scalars=mock_scalars))

        service = SearchService(session)
        assert isinstance(service._backend, PostgresBackend)

        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))
        with patch(
            "genomeai_api.search.backends.postgres._execute_search",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = SearchResult(
                items=["item"], total_count=1, page=1, page_size=10,
            )
            response = await service.search(Study, request)
            assert response.pagination.total_count == 1
            assert response.items == ["item"]

    @pytest.mark.asyncio
    async def test_service_with_custom_backend(self) -> None:
        mock_backend = AsyncMock(spec=SearchBackend)
        mock_backend.search.return_value = SearchResult(
            items=["custom"],
            total_count=1,
            page=1,
            page_size=10,
        )

        service = SearchService(
            session=AsyncMock(),
            backend=mock_backend,
        )
        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))
        response = await service.search(Study, request)
        assert response.pagination.total_count == 1
        assert response.items == ["custom"]

    @pytest.mark.asyncio
    async def test_service_backend_fallback(self) -> None:
        mock_backend = AsyncMock(spec=SearchBackend)
        mock_backend.search.return_value = SearchResult(
            items=["fallback"],
            total_count=1,
            page=1,
            page_size=10,
        )

        service = SearchService(session=AsyncMock(), backend=mock_backend)
        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))
        response = await service.search(Study, request)
        assert response.items == ["fallback"]

    @pytest.mark.asyncio
    async def test_service_suggest_with_backend(self) -> None:
        mock_backend = AsyncMock(spec=SearchBackend)
        mock_backend.suggest.return_value = ["x", "y", "z"]

        service = SearchService(session=AsyncMock(), backend=mock_backend)
        response = await service.suggest(Study, "study_name", "x", limit=3)
        assert response.count == 3
        assert response.suggestions[0].value == "x"


class TestBackendSelection:
    def test_postgres_default(self) -> None:
        session = AsyncMock()
        backend = create_backend(BackendConfig(), session)
        assert isinstance(backend, PostgresBackend)

    def test_opensearch_selection(self) -> None:
        backend = create_backend(BackendConfig(backend="opensearch"))
        assert isinstance(backend, OpenSearchBackend)

    def test_elasticsearch_selection(self) -> None:
        backend = create_backend(BackendConfig(backend="elasticsearch"))
        assert isinstance(backend, ElasticsearchBackend)

    def test_create_backend_from_config(self) -> None:
        config = BackendConfig(backend="opensearch", url="http://localhost:9200")
        backend = create_backend(config)
        assert isinstance(backend, OpenSearchBackend)
        assert backend._hosts == ["http://localhost:9200"]

    def test_custom_url_inherited(self) -> None:
        config = BackendConfig(
            backend="opensearch",
            url="https://myhost:9200",
        )
        backend = create_backend(config)
        assert isinstance(backend, OpenSearchBackend)
        assert backend._hosts == ["https://myhost:9200"]
