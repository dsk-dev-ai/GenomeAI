from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.gene import Gene
from genomeai_api.models.study import Study
from genomeai_api.models.variant import Variant
from genomeai_api.schemas.search import (
    CoordinateIntervalModel,
    CoordinateSearchRequest,
    CoordinateSearchResponse,
    FilterRule,
    PaginationRequest,
    SortRequest,
)
from genomeai_api.search.coordinate_intervals import apply_coordinate_filter
from genomeai_api.search.coordinate_types import CoordinateInterval, CoordinateMatchType
from genomeai_api.search.coordinate_validation import (
    SUPPORTED_COORDINATE_MATCH_TYPES,
    validate_chromosome,
    validate_coordinate,
    validate_coordinate_request,
    validate_interval,
    validate_match_type,
)
from genomeai_api.services.search import SearchService
from pydantic import ValidationError
from sqlalchemy import select


class TestCoordinateMatchType:
    def test_values(self) -> None:
        assert CoordinateMatchType.EXACT.value == "exact"
        assert CoordinateMatchType.CONTAINS.value == "contains"
        assert CoordinateMatchType.CONTAINED_BY.value == "contained_by"
        assert CoordinateMatchType.OVERLAP.value == "overlap"
        assert CoordinateMatchType.RANGE.value == "range"

    def test_all_in_supported_set(self) -> None:
        for t in CoordinateMatchType:
            assert t.value in SUPPORTED_COORDINATE_MATCH_TYPES


class TestCoordinateInterval:
    def test_frozen(self) -> None:
        interval = CoordinateInterval(chromosome="chr1", start=100, end=200)
        assert interval.chromosome == "chr1"
        assert interval.start == 100
        assert interval.end == 200


class TestValidateChromosome:
    def test_valid_chromosomes(self) -> None:
        for chrom in ["1", "chr1", "X", "chrX", "Y", "MT", "M", "22", "chr22", "23"]:
            validate_chromosome(chrom)

    def test_invalid_chromosomes(self) -> None:
        for chrom in ["", "  ", "chr1a", "chrXYZ", "0", "chr0"]:
            with pytest.raises(ValueError, match="(?i)chromosome"):
                validate_chromosome(chrom)


class TestValidateCoordinate:
    def test_valid_coordinates(self) -> None:
        for coord in [0, 1, 100, 999999]:
            validate_coordinate(coord)

    def test_negative_coordinate(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            validate_coordinate(-1)

    def test_non_int(self) -> None:
        with pytest.raises(ValueError, match="integer"):
            validate_coordinate(1.5)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="integer"):
            validate_coordinate("100")  # type: ignore[arg-type]


class TestValidateInterval:
    def test_valid_intervals(self) -> None:
        validate_interval(0, 0)
        validate_interval(100, 200)
        validate_interval(100, 100)

    def test_start_greater_than_end(self) -> None:
        with pytest.raises(ValueError, match="Start.*must not exceed end"):
            validate_interval(200, 100)


class TestValidateMatchType:
    def test_valid_types(self) -> None:
        for t in ["exact", "contains", "contained_by", "overlap", "range"]:
            validate_match_type(t)

    def test_invalid_type(self) -> None:
        with pytest.raises(ValueError, match="Unsupported match type"):
            validate_match_type("invalid")


class TestValidateCoordinateRequest:
    def test_valid_request(self) -> None:
        validate_coordinate_request("chr1", 100, 200, "overlap")

    def test_invalid_chromosome(self) -> None:
        with pytest.raises(ValueError, match="(?i)chromosome"):
            validate_coordinate_request("", 100, 200, "overlap")

    def test_invalid_start(self) -> None:
        with pytest.raises(ValueError, match="start"):
            validate_coordinate_request("chr1", -1, 200, "overlap")

    def test_invalid_end(self) -> None:
        with pytest.raises(ValueError, match="end"):
            validate_coordinate_request("chr1", 100, -1, "overlap")

    def test_invalid_interval(self) -> None:
        with pytest.raises(ValueError, match="Start.*must not exceed end"):
            validate_coordinate_request("chr1", 200, 100, "overlap")

    def test_invalid_match_type(self) -> None:
        with pytest.raises(ValueError, match="Unsupported match type"):
            validate_coordinate_request("chr1", 100, 200, "bad_type")


class TestCoordinateIntervalModel:
    def test_valid(self) -> None:
        m = CoordinateIntervalModel(chromosome="chr1", start=100, end=200)
        assert m.chromosome == "chr1"
        assert m.start == 100
        assert m.end == 200

    def test_start_end_equal(self) -> None:
        m = CoordinateIntervalModel(chromosome="chr1", start=100, end=100)
        assert m.start == 100
        assert m.end == 100

    def test_start_greater_than_end(self) -> None:
        with pytest.raises(ValidationError, match="Start.*must not exceed end"):
            CoordinateIntervalModel(chromosome="chr1", start=200, end=100)

    def test_negative_start(self) -> None:
        with pytest.raises(ValidationError):
            CoordinateIntervalModel(chromosome="chr1", start=-1, end=100)

    def test_empty_chromosome(self) -> None:
        with pytest.raises(ValidationError):
            CoordinateIntervalModel(chromosome="", start=1, end=100)


class TestCoordinateSearchRequest:
    def test_defaults(self) -> None:
        interval = CoordinateIntervalModel(chromosome="chr1", start=100, end=200)
        req = CoordinateSearchRequest(interval=interval)
        assert req.match_type == "overlap"
        assert req.pagination.page == 1
        assert req.pagination.page_size == 20
        assert req.sort is None
        assert req.filters is None
        assert req.chromosome_column == "chromosome"
        assert req.start_column == "start_position"
        assert req.end_column == "end_position"

    def test_custom_values(self) -> None:
        interval = CoordinateIntervalModel(chromosome="X", start=5000, end=10000)
        req = CoordinateSearchRequest(
            interval=interval,
            match_type="exact",
            pagination=PaginationRequest(page=2, page_size=10),
            sort=SortRequest(sort_by="gene_name", sort_order="asc"),
            filters=[FilterRule(field="biotype", operator="equals", value="protein_coding")],
            chromosome_column="chrom",
            start_column="start",
            end_column="stop",
        )
        assert req.match_type == "exact"
        assert req.pagination.page == 2
        assert req.sort is not None
        assert req.sort.sort_by == "gene_name"
        assert req.filters is not None
        assert len(req.filters) == 1
        assert req.chromosome_column == "chrom"
        assert req.start_column == "start"
        assert req.end_column == "stop"


class TestCoordinateSearchResponse:
    def test_empty(self) -> None:
        from genomeai_api.schemas.search import (
            CoordinateSearchResponse,
            PaginationResponse,
        )

        pagination = PaginationResponse(
            page=1, page_size=20, total_count=0, total_pages=1,
            has_next=False, has_previous=False,
        )
        resp = CoordinateSearchResponse(items=[], pagination=pagination)
        assert resp.items == []
        assert resp.pagination.total_count == 0

    def test_with_items(self) -> None:
        from genomeai_api.schemas.search import (
            CoordinateSearchResponse,
            PaginationResponse,
        )

        pagination = PaginationResponse(
            page=1, page_size=20, total_count=2, total_pages=1,
            has_next=False, has_previous=False,
        )
        resp = CoordinateSearchResponse(items=["a", "b"], pagination=pagination)
        assert resp.items == ["a", "b"]
        assert resp.pagination.total_count == 2


class TestApplyCoordinateFilter:
    INTERVAL = CoordinateInterval(chromosome="chr1", start=100, end=200)

    def test_exact(self) -> None:
        stmt = select(Gene)
        result = apply_coordinate_filter(stmt, Gene, self.INTERVAL, CoordinateMatchType.EXACT)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "genes.chromosome" in compiled
        assert "chr1" in compiled
        assert "genes.start_position" in compiled
        assert "genes.end_position" in compiled

    def test_contains(self) -> None:
        stmt = select(Gene)
        result = apply_coordinate_filter(
            stmt, Gene, self.INTERVAL, CoordinateMatchType.CONTAINS
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "genes.chromosome" in compiled
        assert "start_position" in compiled
        assert "end_position" in compiled

    def test_contained_by(self) -> None:
        stmt = select(Gene)
        result = apply_coordinate_filter(
            stmt, Gene, self.INTERVAL, CoordinateMatchType.CONTAINED_BY
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "genes.chromosome" in compiled
        assert "start_position" in compiled
        assert "end_position" in compiled

    def test_overlap(self) -> None:
        stmt = select(Gene)
        result = apply_coordinate_filter(
            stmt, Gene, self.INTERVAL, CoordinateMatchType.OVERLAP
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "genes.chromosome" in compiled
        assert "start_position" in compiled
        assert "end_position" in compiled

    def test_range(self) -> None:
        stmt = select(Gene)
        result = apply_coordinate_filter(
            stmt, Gene, self.INTERVAL, CoordinateMatchType.RANGE
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "genes.chromosome" in compiled
        assert "start_position" in compiled
        assert "end_position" in compiled

    def test_custom_columns(self) -> None:
        stmt = select(Gene)
        result = apply_coordinate_filter(
            stmt, Gene, self.INTERVAL, CoordinateMatchType.EXACT,
            chromosome_column="gene_id",
            start_column="gene_id",
            end_column="gene_id",
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "genes.gene_id" in compiled

    def test_unsupported_type_raises(self) -> None:
        stmt = select(Gene)
        with pytest.raises(ValueError, match="Unsupported match type"):
            apply_coordinate_filter(
                stmt, Gene, self.INTERVAL, "bad_type",  # type: ignore[arg-type]
            )

    def test_variant_single_position(self) -> None:
        """Variant has 'position' column instead of start/end."""
        interval = CoordinateInterval(chromosome="chr1", start=150, end=150)
        stmt = select(Variant)
        result = apply_coordinate_filter(
            stmt, Variant, interval, CoordinateMatchType.EXACT,
            start_column="position",
            end_column="position",
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "variants.chromosome" in compiled
        assert "variants.position" in compiled
        assert "variants.position" in compiled

    def test_no_chromosome_filter_on_mismatch(self) -> None:
        """Different chromosomes don't match."""
        interval = CoordinateInterval(chromosome="chr2", start=100, end=200)
        stmt = select(Gene)
        result = apply_coordinate_filter(
            stmt, Gene, interval, CoordinateMatchType.OVERLAP
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "chr2" in compiled

    def test_boundary_overlap(self) -> None:
        """Exact boundary overlap still overlaps."""
        interval = CoordinateInterval(chromosome="chr1", start=200, end=300)
        stmt = select(Gene)
        result = apply_coordinate_filter(
            stmt, Gene, interval, CoordinateMatchType.OVERLAP
        )
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "start_position" in compiled


class TestCoordinateSearchService:
    @pytest.mark.asyncio
    async def test_basic_coordinate_search(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 3

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["g1", "g2", "g3"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="chr1", start=10000, end=20000)
        request = CoordinateSearchRequest(interval=interval)
        service = SearchService(session)
        result = await service.coordinate_search(Gene, request)
        assert isinstance(result, CoordinateSearchResponse)
        assert result.pagination.total_count == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_coordinate_search_empty(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        data_scalar = MagicMock()
        data_scalar.all.return_value = []
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="chr22", start=1, end=100)
        request = CoordinateSearchRequest(interval=interval)
        service = SearchService(session)
        result = await service.coordinate_search(Gene, request)
        assert result.pagination.total_count == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_coordinate_search_with_filters(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["g1"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="chr1", start=100, end=200)
        request = CoordinateSearchRequest(
            interval=interval,
            match_type="exact",
            filters=[FilterRule(field="biotype", operator="equals", value="protein_coding")],
        )
        service = SearchService(session)
        result = await service.coordinate_search(Gene, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_coordinate_search_with_sort(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 5

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["g1", "g2"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="chr1", start=0, end=999999)
        request = CoordinateSearchRequest(
            interval=interval,
            sort=SortRequest(sort_by="gene_name", sort_order="asc"),
        )
        service = SearchService(session)
        result = await service.coordinate_search(Gene, request)
        assert result.pagination.total_count == 5

    @pytest.mark.asyncio
    async def test_coordinate_search_with_pagination(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 100

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["g1", "g2"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="chr1", start=0, end=999999)
        request = CoordinateSearchRequest(
            interval=interval,
            pagination=PaginationRequest(page=3, page_size=10),
        )
        service = SearchService(session)
        result = await service.coordinate_search(Gene, request)
        assert result.pagination.page == 3
        assert result.pagination.page_size == 10
        assert result.pagination.total_count == 100

    @pytest.mark.asyncio
    async def test_coordinate_search_invalid_field_filter(self) -> None:
        session = AsyncMock(spec=["execute"])
        interval = CoordinateIntervalModel(chromosome="chr1", start=0, end=100)
        request = CoordinateSearchRequest(
            interval=interval,
            filters=[FilterRule(field="nonexistent", operator="equals", value="x")],
        )
        service = SearchService(session)
        with pytest.raises(ValueError, match="Invalid filter field"):
            await service.coordinate_search(Gene, request)

    @pytest.mark.asyncio
    async def test_coordinate_search_invalid_sort_field(self) -> None:
        session = AsyncMock(spec=["execute"])
        interval = CoordinateIntervalModel(chromosome="chr1", start=0, end=100)
        request = CoordinateSearchRequest(
            interval=interval,
            sort=SortRequest(sort_by="nonexistent", sort_order="asc"),
        )
        service = SearchService(session)
        with pytest.raises(ValueError, match="Invalid sort field"):
            await service.coordinate_search(Gene, request)

    @pytest.mark.asyncio
    async def test_coordinate_search_with_base_stmt(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["g_a", "g_b"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="chr1", start=5000, end=15000)
        request = CoordinateSearchRequest(interval=interval)
        base_stmt = select(Gene).where(Gene.biotype == "protein_coding")
        service = SearchService(session)
        result = await service.coordinate_search(Gene, request, base_stmt=base_stmt)
        assert result.pagination.total_count == 2

    @pytest.mark.asyncio
    async def test_coordinate_search_variant_single_position(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["v1"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="chr1", start=150, end=150)
        request = CoordinateSearchRequest(
            interval=interval,
            match_type="exact",
            start_column="position",
            end_column="position",
        )
        service = SearchService(session)
        result = await service.coordinate_search(Variant, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_coordinate_search_non_coordinate_model(self) -> None:
        """Study has no coordinate columns — should work with custom column mapping."""
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["s1", "s2"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        interval = CoordinateIntervalModel(chromosome="PRJ", start=1, end=100)
        request = CoordinateSearchRequest(
            interval=interval,
            chromosome_column="study_id",
            start_column="study_id",
            end_column="study_id",
        )
        service = SearchService(session)
        result = await service.coordinate_search(Study, request)
        assert result.pagination.total_count == 2
