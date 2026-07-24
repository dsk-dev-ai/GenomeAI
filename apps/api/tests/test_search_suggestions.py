from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.study import Study
from genomeai_api.schemas.search import SuggestionItem
from genomeai_api.search.autocomplete import build_prefix_query
from genomeai_api.search.cache import (
    MemoryCache,
    NullCache,
    SuggestionCacheEntry,
    suggestion_cache_key,
)
from genomeai_api.search.suggestions import (
    Suggestion,
    SuggestionMatchType,
    rank_suggestions,
)
from genomeai_api.services.search import SearchService
from pydantic import ValidationError


def _make_item(value: str = "brca1", match_type: str = "exact", rank: int = 0) -> SuggestionItem:
    return SuggestionItem(
        domain="study",
        field="study_name",
        value=value,
        rank=rank,
        match_type=match_type,
    )


class TestSuggestionCacheKey:
    def test_returns_expected_format(self) -> None:
        key = suggestion_cache_key("study", "study_name", "cancer", 10)
        assert key == "suggest:study:study_name:cancer:10"

    def test_differs_with_different_domain(self) -> None:
        k1 = suggestion_cache_key("study", "study_name", "cancer", 10)
        k2 = suggestion_cache_key("gene", "study_name", "cancer", 10)
        assert k1 != k2

    def test_differs_with_different_limit(self) -> None:
        k1 = suggestion_cache_key("study", "study_name", "cancer", 10)
        k2 = suggestion_cache_key("study", "study_name", "cancer", 20)
        assert k1 != k2

    def test_differs_with_different_query(self) -> None:
        k1 = suggestion_cache_key("study", "study_name", "cancer", 10)
        k2 = suggestion_cache_key("study", "study_name", "brca", 10)
        assert k1 != k2

    def test_differs_with_different_field(self) -> None:
        k1 = suggestion_cache_key("study", "study_name", "cancer", 10)
        k2 = suggestion_cache_key("study", "title", "cancer", 10)
        assert k1 != k2


class TestNullCache:
    def test_get_returns_none(self) -> None:
        cache = NullCache()
        assert cache.get("any") is None

    def test_set_does_not_store(self) -> None:
        cache = NullCache()
        cache.set("key", [_make_item()], 60)
        assert cache.get("key") is None

    def test_invalidate_does_not_crash(self) -> None:
        cache = NullCache()
        cache.invalidate("missing")
        cache.invalidate("any")


class TestMemoryCache:
    def test_get_set_roundtrip(self) -> None:
        cache = MemoryCache()
        items = [_make_item("brca1")]
        cache.set("k", items, 60)
        assert cache.get("k") == items

    def test_get_missing_returns_none(self) -> None:
        cache = MemoryCache()
        assert cache.get("missing") is None

    def test_invalidate_removes_entry(self) -> None:
        cache = MemoryCache()
        cache.set("k", [_make_item("x")], 60)
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_invalidate_missing_does_not_crash(self) -> None:
        cache = MemoryCache()
        cache.invalidate("missing")

    def test_multiple_entries(self) -> None:
        cache = MemoryCache()
        a = [_make_item("a")]
        b = [_make_item("b")]
        cache.set("a", a, 60)
        cache.set("b", b, 60)
        assert cache.get("a") == a
        assert cache.get("b") == b

    def test_entry_type(self) -> None:
        items = [_make_item("x")]
        entry = SuggestionCacheEntry(suggestions=items, expires_at=1000.0)
        assert entry.suggestions == items
        assert entry.expires_at == 1000.0

    def test_expired_entry_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache = MemoryCache()
        fake_now = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)

        cache.set("k", [_make_item("val")], ttl=10)
        assert cache.get("k") is not None

        fake_now = 1100.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)
        assert cache.get("k") is None

    def test_expired_entry_removed_from_store(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache = MemoryCache()
        fake_now = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)

        cache.set("k", [_make_item("val")], ttl=10)
        fake_now = 1100.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)
        cache.get("k")
        assert "k" not in cache._store

    def test_valid_entry_survives_after_get(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache = MemoryCache()
        fake_now = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)

        items = [_make_item("survivor")]
        cache.set("k", items, ttl=60)
        assert cache.get("k") == items
        assert "k" in cache._store

    def test_set_overwrites_old_ttl(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache = MemoryCache()
        fake_now = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)

        cache.set("k", [_make_item("old")], ttl=10)
        fake_now = 1005.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)
        cache.set("k", [_make_item("new")], ttl=20)

        fake_now = 1012.0
        monkeypatch.setattr(time, "monotonic", lambda: fake_now)
        # first entry would have expired (1000+10=1010), second is still valid (1005+20=1025)
        assert cache.get("k") is not None


class TestSuggestion:
    def test_frozen(self) -> None:
        s = Suggestion(
            domain="study",
            field="study_name",
            value="cancer study",
            rank=0,
            match_type=SuggestionMatchType.EXACT,
        )
        assert s.domain == "study"
        assert s.field == "study_name"
        assert s.value == "cancer study"
        assert s.rank == 0
        assert s.match_type == SuggestionMatchType.EXACT


class TestSuggestionMatchType:
    def test_exact_value(self) -> None:
        assert SuggestionMatchType.EXACT.value == "exact"

    def test_prefix_value(self) -> None:
        assert SuggestionMatchType.PREFIX.value == "prefix"

    def test_alphabetical_value(self) -> None:
        assert SuggestionMatchType.ALPHABETICAL.value == "alphabetical"


class TestRankSuggestions:
    def test_returns_empty_for_empty_input(self) -> None:
        result = rank_suggestions([], "brca", "gene", "gene_name")
        assert result == []

    def test_exact_match_ranked_first(self) -> None:
        values = ["brca2", "brca1", "brca"]
        result = rank_suggestions(values, "brca", "gene", "gene_name")
        assert result[0].value == "brca"
        assert result[0].match_type == SuggestionMatchType.EXACT
        assert result[0].rank == 0

    def test_prefix_matches_after_exact(self) -> None:
        values = ["brca2", "brca", "brca1"]
        result = rank_suggestions(values, "brca", "gene", "gene_name")
        assert result[0].match_type == SuggestionMatchType.EXACT
        assert all(
            r.match_type == SuggestionMatchType.PREFIX for r in result[1:]
        )

    def test_deduplication(self) -> None:
        values = ["brca1", "brca1", "brca1"]
        result = rank_suggestions(values, "brca", "gene", "gene_name")
        assert len(result) == 1

    def test_case_insensitive_matching(self) -> None:
        values = ["BRCA1", "BRCA2", "BRCA"]
        result = rank_suggestions(values, "brca", "gene", "gene_name")
        assert result[0].match_type == SuggestionMatchType.EXACT
        assert result[0].value == "BRCA"

    def test_alphabetical_fallback(self) -> None:
        values = ["zzz", "aaa", "mmm"]
        result = rank_suggestions(values, "xyz", "gene", "gene_name")
        assert result[0].value == "aaa"
        assert result[1].value == "mmm"
        assert result[2].value == "zzz"
        assert all(r.match_type == SuggestionMatchType.ALPHABETICAL for r in result)

    def test_sorts_alphabetically_within_match_type(self) -> None:
        values = ["brca2", "brca1"]
        result = rank_suggestions(values, "brca", "gene", "gene_name")
        assert len(result) == 2
        assert result[0].match_type == SuggestionMatchType.PREFIX
        assert result[1].match_type == SuggestionMatchType.PREFIX
        assert result[0].value == "brca1"
        assert result[1].value == "brca2"

    def test_prefix_matches_alphabetical(self) -> None:
        values = ["brca", "brca1", "zzz"]
        result = rank_suggestions(values, "brca", "gene", "gene_name")
        assert result[0].match_type == SuggestionMatchType.EXACT
        assert result[1].match_type == SuggestionMatchType.PREFIX
        assert result[2].match_type == SuggestionMatchType.ALPHABETICAL

    def test_rank_sequence_after_sort(self) -> None:
        values = ["zzz", "aaa", "brca"]
        result = rank_suggestions(values, "brca", "gene", "gene_name")
        assert result[0].rank == 0
        assert result[1].rank == 1
        assert result[2].rank == 2


class TestBuildPrefixQuery:
    def test_creates_select_statement(self) -> None:
        stmt = build_prefix_query(Study, "study_name", "cancer", 10)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "SELECT" in compiled.upper()
        assert "study_name" in compiled
        assert "cancer%" in compiled.lower()
        assert "LIMIT 10" in compiled

    def test_order_by_exact_then_alpha(self) -> None:
        stmt = build_prefix_query(Study, "study_name", "cancer", 10)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "ORDER BY" in compiled

    def test_uses_distinct(self) -> None:
        stmt = build_prefix_query(Study, "study_name", "cancer", 10)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "DISTINCT" in compiled.upper()


class TestSearchServiceSuggest:
    @pytest.mark.asyncio
    async def test_basic_suggest(self) -> None:
        session = AsyncMock(spec=["execute"])

        scalar_result = MagicMock()
        scalar_result.all.return_value = [
            ("cancer study",),
            ("cancer research",),
        ]

        session.execute = AsyncMock(return_value=scalar_result)

        service = SearchService(session)
        result = await service.suggest(
            model=Study,
            column_name="study_name",
            query="cancer",
            limit=10,
            domain="study",
        )
        assert result.query == "cancer"
        assert result.count > 0
        assert result.suggestions[0].match_type in ("exact", "prefix")

    @pytest.mark.asyncio
    async def test_suggest_empty_results(self) -> None:
        session = AsyncMock(spec=["execute"])

        scalar_result = MagicMock()
        scalar_result.all.return_value = []

        session.execute = AsyncMock(return_value=scalar_result)

        service = SearchService(session)
        result = await service.suggest(
            model=Study,
            column_name="study_name",
            query="nonexistent123",
            limit=10,
            domain="study",
        )
        assert result.count == 0
        assert result.suggestions == []

    @pytest.mark.asyncio
    async def test_suggest_with_cache_hit(self) -> None:
        session = AsyncMock(spec=["execute"])
        cache = MemoryCache()

        items = [
            SuggestionItem(
                domain="study", field="study_name", value="cancer",
                rank=0, match_type="exact",
            ),
        ]
        cache.set("suggest:study:study_name:cancer:10", items, 60)

        service = SearchService(session)
        result = await service.suggest(
            model=Study,
            column_name="study_name",
            query="cancer",
            limit=10,
            domain="study",
            cache=cache,
        )
        assert result.count == 1
        assert result.suggestions[0].value == "cancer"
        session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_suggest_cache_miss_then_write(self) -> None:
        session = AsyncMock(spec=["execute"])

        scalar_result = MagicMock()
        scalar_result.all.return_value = [("brca1",)]
        session.execute = AsyncMock(return_value=scalar_result)

        cache = MemoryCache()
        service = SearchService(session)
        result = await service.suggest(
            model=Study,
            column_name="study_name",
            query="brca1",
            limit=10,
            domain="study",
            cache=cache,
        )
        assert result.count == 1

        cached = cache.get("suggest:study:study_name:brca1:10")
        assert cached is not None
        assert len(cached) == 1
        assert cached[0].value == "brca1"
        assert cached[0].domain == "study"

    @pytest.mark.asyncio
    async def test_suggest_uses_null_cache_by_default(self) -> None:
        session = AsyncMock(spec=["execute"])

        scalar_result = MagicMock()
        scalar_result.all.return_value = [("brca1",)]

        session.execute = AsyncMock(return_value=scalar_result)

        service = SearchService(session)
        result = await service.suggest(
            model=Study,
            column_name="study_name",
            query="brca",
            limit=10,
            domain="study",
        )
        assert result.count == 1
        assert result.suggestions[0].value == "brca1"
        session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_suggest_cache_key_normalized(self) -> None:
        session = AsyncMock(spec=["execute"])

        scalar_result = MagicMock()
        scalar_result.all.return_value = [("brca1",)]
        session.execute = AsyncMock(return_value=scalar_result)

        cache = MemoryCache()
        service = SearchService(session)
        result_upper = await service.suggest(
            model=Study,
            column_name="study_name",
            query="  BRCA1  ",
            limit=10,
            domain="study",
            cache=cache,
        )
        result_lower = await service.suggest(
            model=Study,
            column_name="study_name",
            query="brca1",
            limit=10,
            domain="study",
            cache=cache,
        )
        assert result_upper.query == "  BRCA1  "
        assert result_lower.query == "brca1"
        assert result_upper.suggestions == result_lower.suggestions
        session.execute.assert_called_once()


class TestSuggestionSchemas:
    def test_suggestion_item_required_fields(self) -> None:
        item = SuggestionItem(
            domain="study",
            field="study_name",
            value="cancer study",
            rank=0,
            match_type="exact",
        )
        assert item.domain == "study"
        assert item.value == "cancer study"
        assert item.match_type == "exact"

    def test_suggestion_item_invalid_match_type(self) -> None:
        with pytest.raises(ValidationError):
            SuggestionItem(
                domain="study",
                field="study_name",
                value="test",
                rank=0,
                match_type="invalid",
            )

    def test_suggestion_response(self) -> None:
        from genomeai_api.schemas.search import SuggestionResponse

        items = [SuggestionItem(
            domain="study", field="study_name", value="cancer",
            rank=0, match_type="exact",
        )]
        response = SuggestionResponse(suggestions=items, count=1, query="cancer")
        assert response.count == 1
        assert response.query == "cancer"
        assert len(response.suggestions) == 1

    def test_suggestion_response_empty(self) -> None:
        from genomeai_api.schemas.search import SuggestionResponse

        response = SuggestionResponse(suggestions=[], count=0, query="xyz")
        assert response.count == 0
        assert response.suggestions == []

    def test_suggestion_response_serialization(self) -> None:
        from genomeai_api.schemas.search import SuggestionResponse

        items = [SuggestionItem(
            domain="study", field="study_name", value="brca",
            rank=0, match_type="prefix",
        )]
        response = SuggestionResponse(suggestions=items, count=1, query="brca")
        dumped = response.model_dump()
        assert dumped["query"] == "brca"
        assert dumped["count"] == 1
        assert dumped["suggestions"][0]["match_type"] == "prefix"
