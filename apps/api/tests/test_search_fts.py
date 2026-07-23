from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.study import Study
from genomeai_api.repositories.search import execute_fts_search
from genomeai_api.schemas.search import (
    FilterRule,
    FullTextSearchConfig,
    FullTextSearchRequest,
    FullTextSearchResponse,
    HighlightedMatch,
    PaginationRequest,
    PaginationResponse,
    QueryType,
    RankedSearchResult,
    SearchRequest,
    WeightType,
)
from genomeai_api.search.fts import build_tsquery, build_tsvector
from genomeai_api.search.highlighting import apply_ts_headlines, build_ts_headline
from genomeai_api.search.indexes import (
    create_gin_index,
    create_tsvector_column,
    create_tsvector_index,
)
from genomeai_api.search.query import apply_fts_filter, apply_fts_to_statement
from genomeai_api.search.ranking import apply_ts_rank, apply_ts_rank_cd, order_by_rank_desc
from genomeai_api.services.search import SearchService
from sqlalchemy import select


class TestBuildTSVector:
    def test_single_column(self) -> None:
        vec = build_tsvector([Study.study_name])
        compiled = str(vec.compile(compile_kwargs={"literal_binds": True}))
        assert "to_tsvector" in compiled
        assert "study_name" in compiled

    def test_multiple_columns(self) -> None:
        vec = build_tsvector([Study.study_name, Study.description])
        compiled = str(vec.compile(compile_kwargs={"literal_binds": True}))
        assert "to_tsvector" in compiled
        assert "study_name" in compiled
        assert "description" in compiled
        assert "||" in compiled

    def test_with_weights(self) -> None:
        vec = build_tsvector(
            [Study.study_name, Study.description],
            weights=["A", "B"],
        )
        compiled = str(vec.compile(compile_kwargs={"literal_binds": True}))
        assert "setweight" in compiled

    def test_weights_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="Number of weights"):
            build_tsvector([Study.study_name], weights=["A", "B"])

    def test_empty_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="At least one column"):
            build_tsvector([])

    def test_with_config(self) -> None:
        vec = build_tsvector([Study.study_name], config="french")
        compiled = str(vec.compile())
        assert "to_tsvector" in compiled
        assert "studies.study_name" in compiled


class TestBuildTSQuery:
    def test_plain(self) -> None:
        q = build_tsquery("cancer research")
        compiled = str(q.compile(compile_kwargs={"literal_binds": True}))
        assert "plainto_tsquery" in compiled

    def test_phrase(self) -> None:
        q = build_tsquery("cancer research", query_type="phrase")
        compiled = str(q.compile(compile_kwargs={"literal_binds": True}))
        assert "phraseto_tsquery" in compiled

    def test_websearch(self) -> None:
        q = build_tsquery("cancer research", query_type="websearch")
        compiled = str(q.compile(compile_kwargs={"literal_binds": True}))
        assert "websearch_to_tsquery" in compiled

    def test_raw(self) -> None:
        q = build_tsquery("cancer & research", query_type="raw")
        compiled = str(q.compile(compile_kwargs={"literal_binds": True}))
        assert "to_tsquery" in compiled

    def test_with_config(self) -> None:
        q = build_tsquery("cancer", config="french")
        compiled = str(q.compile())
        assert "plainto_tsquery" in compiled

    def test_empty_query_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            build_tsquery("")

    def test_whitespace_query_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            build_tsquery("   ")

    def test_unknown_query_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown query type"):
            build_tsquery("test", query_type="invalid")  # type: ignore[arg-type]


class TestApplyFTSFilter:
    def test_applies_fts_filter(self) -> None:
        stmt = select(Study)
        vec = build_tsvector([Study.study_name])
        q = build_tsquery("cancer")
        result = apply_fts_filter(stmt, vec, q)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "@@" in compiled

    def test_apply_fts_to_statement(self) -> None:
        stmt = select(Study)
        result = apply_fts_to_statement(
            stmt, Study, ["study_name", "description"], "cancer",
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "to_tsvector" in compiled
        assert "plainto_tsquery" in compiled
        assert "@@" in compiled

    def test_apply_fts_to_statement_with_weights(self) -> None:
        stmt = select(Study)
        result = apply_fts_to_statement(
            stmt, Study, ["study_name", "description"], "cancer",
            weights=["A", "B"],
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "setweight" in compiled


class TestRanking:
    def test_apply_ts_rank(self) -> None:
        stmt = select(Study)
        vec = build_tsvector([Study.study_name])
        q = build_tsquery("cancer")
        result = apply_ts_rank(stmt, vec, q, label="my_rank")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "ts_rank" in compiled
        assert "my_rank" in compiled

    def test_apply_ts_rank_cd(self) -> None:
        stmt = select(Study)
        vec = build_tsvector([Study.study_name])
        q = build_tsquery("cancer")
        result = apply_ts_rank_cd(stmt, vec, q, label="cd_rank")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "ts_rank_cd" in compiled
        assert "cd_rank" in compiled

    def test_order_by_rank_desc(self) -> None:
        stmt = select(Study)
        result = order_by_rank_desc(stmt, rank_label="my_rank")
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "my_rank" in compiled
        assert "DESC" in compiled.upper()

    def test_ranking_with_normalization(self) -> None:
        stmt = select(Study)
        vec = build_tsvector([Study.study_name])
        q = build_tsquery("cancer")
        result = apply_ts_rank(stmt, vec, q, normalization=32)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "32" in compiled


class TestHighlighting:
    def test_build_ts_headline(self) -> None:
        q = build_tsquery("cancer")
        hl = build_ts_headline(Study.description, q)
        compiled = str(hl.compile(compile_kwargs={"literal_binds": True}))
        assert "ts_headline" in compiled

    def test_build_ts_headline_with_options(self) -> None:
        q = build_tsquery("cancer")
        hl = build_ts_headline(Study.description, q, options="MaxWords=20,MinWords=5")
        compiled = str(hl.compile(compile_kwargs={"literal_binds": True}))
        assert "MaxWords" in compiled

    def test_apply_ts_headlines(self) -> None:
        stmt = select(Study)
        q = build_tsquery("cancer")
        result = apply_ts_headlines(stmt, Study, ["description"], q)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "ts_headline" in compiled
        assert "description_highlight" in compiled

    def test_apply_ts_headlines_multiple_columns(self) -> None:
        stmt = select(Study)
        q = build_tsquery("cancer")
        result = apply_ts_headlines(
            stmt, Study, ["study_name", "description"], q,
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "study_name_highlight" in compiled
        assert "description_highlight" in compiled


class TestIndexes:
    def test_create_gin_index(self) -> None:
        idx = create_gin_index("ix_study_name_gin", "studies", "study_name")
        assert idx.name == "ix_study_name_gin"
        assert idx.dialect_kwargs.get("postgresql_using") == "gin"

    def test_create_tsvector_index(self) -> None:
        idx = create_tsvector_index("ix_study_tsv", "studies", "tsv_column")
        assert idx.name == "ix_study_tsv"
        assert idx.dialect_kwargs.get("postgresql_using") == "gin"

    def test_create_tsvector_column(self) -> None:
        col = create_tsvector_column("tsv", "to_tsvector('english', study_name)")
        assert col.name == "tsv"
        assert col.type.__class__.__name__ == "TSVECTOR"
        assert col.default is None


class TestFTSSchemas:
    def test_full_text_search_config_defaults(self) -> None:
        cfg = FullTextSearchConfig(query="cancer", columns=["study_name"])
        assert cfg.query == "cancer"
        assert cfg.config == "english"
        assert cfg.query_type == "plain"
        assert cfg.columns == ["study_name"]
        assert cfg.weights is None

    def test_full_text_search_config_custom(self) -> None:
        cfg = FullTextSearchConfig(
            query="cancer research",
            config="french",
            query_type="phrase",
            columns=["study_name", "description"],
            weights=["A", "B"],
        )
        assert cfg.query_type == "phrase"
        assert cfg.config == "french"

    def test_full_text_search_config_empty_query_raises(self) -> None:
        with pytest.raises(ValueError):
            FullTextSearchConfig(query="", columns=["study_name"])

    def test_full_text_search_config_empty_columns_raises(self) -> None:
        with pytest.raises(ValueError):
            FullTextSearchConfig(query="cancer", columns=[])

    def test_full_text_search_request(self) -> None:
        req = FullTextSearchRequest(
            search=SearchRequest(),
            fts=FullTextSearchConfig(query="cancer", columns=["study_name"]),
        )
        assert req.search.pagination.page == 1
        assert req.fts.query == "cancer"

    def test_highlighted_match(self) -> None:
        hm = HighlightedMatch(field="description", snippet="<b>cancer</b> research")
        assert hm.field == "description"
        assert hm.snippet == "<b>cancer</b> research"

    def test_ranked_search_result(self) -> None:
        rs = RankedSearchResult(rank=0.5)
        assert rs.rank == 0.5
        assert rs.highlights is None

    def test_ranked_search_result_with_highlights(self) -> None:
        rs = RankedSearchResult(
            rank=0.8,
            highlights=[HighlightedMatch(field="name", snippet="<b>cancer</b>")],
        )
        assert rs.rank == 0.8
        assert len(rs.highlights) == 1

    def test_full_text_search_response(self) -> None:
        pagination = PaginationResponse(
            page=1, page_size=20, total_count=2, total_pages=1,
            has_next=False, has_previous=False,
        )
        resp = FullTextSearchResponse(
            items=["a", "b"],
            pagination=pagination,
            ranks=[0.9, 0.5],
            highlights=None,
        )
        assert resp.ranks == [0.9, 0.5]
        assert resp.highlights is None

    def test_full_text_search_response_with_highlights(self) -> None:
        pagination = PaginationResponse(
            page=1, page_size=20, total_count=1, total_pages=1,
            has_next=False, has_previous=False,
        )
        resp = FullTextSearchResponse(
            items=["x"],
            pagination=pagination,
            ranks=[0.9],
            highlights=[
                [HighlightedMatch(field="name", snippet="<b>cancer</b>")],
            ],
        )
        assert len(resp.highlights) == 1
        assert resp.highlights[0][0].field == "name"


class TestExecuteFTSSearch:
    @pytest.mark.asyncio
    async def test_basic_fts_search(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        row = MagicMock()
        row._mapping = {
            Study.__tablename__: "item1",
            "_rank": 0.5,
        }
        row.__getitem__ = lambda self, key: "item1"

        session.execute = AsyncMock(return_value=count_result)
        count_side_effect = [count_result]
        count_side_effect.append(
            MagicMock(all=MagicMock(return_value=[row, row]))
        )
        session.execute = AsyncMock(side_effect=count_side_effect)
        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[row, row])),
            ]
        )

        request = SearchRequest()
        result = await execute_fts_search(
            session, Study, request,
            fts_columns=["study_name"],
            fts_query="cancer",
        )

        assert result.total_count == 2
        assert len(result.items) == 2
        assert result.ranks is not None
        assert len(result.ranks) == 2

    @pytest.mark.asyncio
    async def test_fts_search_with_filters(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        row = MagicMock()
        row._mapping = {
            Study.__tablename__: "item1",
            "_rank": 0.8,
        }

        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[row])),
            ]
        )

        request = SearchRequest(
            filters=[FilterRule(field="status", operator="equals", value="active")],
        )
        result = await execute_fts_search(
            session, Study, request,
            fts_columns=["study_name"],
            fts_query="cancer",
        )

        assert result.total_count == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_fts_search_empty_result(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[])),
            ]
        )

        request = SearchRequest()
        result = await execute_fts_search(
            session, Study, request,
            fts_columns=["study_name"],
            fts_query="cancer",
        )

        assert result.total_count == 0
        assert result.items == []
        assert result.ranks == []

    @pytest.mark.asyncio
    async def test_fts_search_with_highlights(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        row = MagicMock()
        row._mapping = {
            Study.__tablename__: "item1",
            "_rank": 0.9,
            "study_name_highlight": "<b>Cancer</b> Study",
        }

        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[row])),
            ]
        )

        request = SearchRequest()
        result = await execute_fts_search(
            session, Study, request,
            fts_columns=["study_name"],
            fts_query="cancer",
            highlight_columns=["study_name"],
        )

        assert result.highlights is not None
        assert len(result.highlights) == 1
        assert result.highlights[0][0] == ("study_name", "<b>Cancer</b> Study")

    @pytest.mark.asyncio
    async def test_fts_search_with_sort(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        row = MagicMock()
        row._mapping = {
            Study.__tablename__: "item1",
            "_rank": 0.9,
        }

        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[row])),
            ]
        )

        request = SearchRequest(
            sort={"sort_by": "study_id", "sort_order": "desc"},
        )
        result = await execute_fts_search(
            session, Study, request,
            fts_columns=["study_name"],
            fts_query="cancer",
        )

        assert result.total_count == 1


class TestFTSQueryTypes:
    def test_query_type_literal_values(self) -> None:
        qt: QueryType = "plain"
        assert qt == "plain"
        qt = "phrase"
        assert qt == "phrase"
        qt = "websearch"
        assert qt == "websearch"
        qt = "raw"
        assert qt == "raw"

    def test_query_type_in_schema(self) -> None:
        from genomeai_api.schemas.search import QueryType as SchemaQueryType
        assert SchemaQueryType.__args__ == ("plain", "phrase", "websearch", "raw")


class TestSearchServiceFTS:
    @pytest.mark.asyncio
    async def test_search_fts_returns_fts_response(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        row = MagicMock()
        row._mapping = {
            Study.__tablename__: "item1",
            "_rank": 0.5,
        }

        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[row])),
            ]
        )

        service = SearchService(session)
        fts_config = FullTextSearchConfig(
            query="cancer",
            columns=["study_name"],
        )
        request = SearchRequest(
            pagination=PaginationRequest(page=1, page_size=10),
        )
        result = await service.search_fts(Study, request, fts_config)

        assert isinstance(result, FullTextSearchResponse)
        assert result.items == ["item1"]
        assert result.ranks == [0.5]
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_search_fts_with_highlights(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        row = MagicMock()
        row._mapping = {
            Study.__tablename__: "item1",
            "_rank": 0.9,
            "study_name_highlight": "<b>Cancer</b>",
        }

        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[row])),
            ]
        )

        service = SearchService(session)
        fts_config = FullTextSearchConfig(
            query="cancer",
            columns=["study_name"],
        )
        request = SearchRequest()
        result = await service.search_fts(Study, request, fts_config)

        assert result.highlights is not None
        assert len(result.highlights) == 1
        assert result.highlights[0][0].field == "study_name"

    @pytest.mark.asyncio
    async def test_search_fts_empty(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        session.execute = AsyncMock(
            side_effect=[
                count_result,
                MagicMock(all=MagicMock(return_value=[])),
            ]
        )

        service = SearchService(session)
        fts_config = FullTextSearchConfig(
            query="cancer",
            columns=["study_name"],
        )
        request = SearchRequest()
        result = await service.search_fts(Study, request, fts_config)

        assert result.items == []
        assert result.ranks == []
        assert result.highlights == []


class TestInvalidFTSColumns:
    @pytest.mark.asyncio
    async def test_invalid_fts_column_raises(self) -> None:
        session = AsyncMock(spec=["execute"])
        request = SearchRequest()
        with pytest.raises(ValueError, match="Invalid FTS column"):
            await execute_fts_search(
                session, Study, request,
                fts_columns=["nonexistent"],
                fts_query="cancer",
            )

    @pytest.mark.asyncio
    async def test_invalid_highlight_column_raises(self) -> None:
        session = AsyncMock(spec=["execute"])
        request = SearchRequest()
        with pytest.raises(ValueError, match="Invalid highlight column"):
            await execute_fts_search(
                session, Study, request,
                fts_columns=["study_name"],
                fts_query="cancer",
                highlight_columns=["nonexistent"],
            )


class TestInvalidWeights:
    def test_invalid_weight_value_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid weight"):
            build_tsvector([Study.study_name], weights=["X"])  # type: ignore[arg-type]

    def test_weight_arity_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="Number of weights"):
            build_tsvector([Study.study_name, Study.description], weights=["A"])

    def test_schema_accepts_valid_weight_type(self) -> None:
        w: WeightType = "A"
        assert w == "A"
        w = "D"
        assert w == "D"

    def test_schema_invalid_weight_arity(self) -> None:
        with pytest.raises(ValueError, match="Number of weights"):
            FullTextSearchConfig(
                query="cancer",
                columns=["study_name", "description"],
                weights=["A"],
            )


class TestWhitespaceQuery:
    def test_whitespace_only_query_raises_in_schema(self) -> None:
        with pytest.raises(ValueError, match="whitespace-only"):
            FullTextSearchConfig(query="   ", columns=["study_name"])

    def test_query_with_leading_trailing_spaces_is_ok(self) -> None:
        cfg = FullTextSearchConfig(
            query="  cancer research  ",
            columns=["study_name"],
        )
        assert cfg.query == "  cancer research  "

    def test_whitespace_only_raises_in_build_tsquery(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            build_tsquery("   ")


class TestNullableColumns:
    def test_coalesce_added_for_single_column(self) -> None:
        vec = build_tsvector([Study.study_name])
        compiled = str(vec.compile(compile_kwargs={"literal_binds": True}))
        assert "coalesce" in compiled
        assert "study_name" in compiled

    def test_coalesce_added_for_multiple_columns(self) -> None:
        vec = build_tsvector([Study.study_name, Study.description])
        compiled = str(vec.compile(compile_kwargs={"literal_binds": True}))
        assert "coalesce" in compiled
        assert "study_name" in compiled
        assert "description" in compiled
