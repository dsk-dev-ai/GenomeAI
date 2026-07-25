from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.dataset import Dataset
from genomeai_api.models.experiment import Experiment
from genomeai_api.models.gene import Gene
from genomeai_api.models.genome import Genome
from genomeai_api.models.project import Project
from genomeai_api.models.protein import Protein
from genomeai_api.models.sample import Sample
from genomeai_api.models.study import Study
from genomeai_api.models.transcript import Transcript
from genomeai_api.models.variant import Variant
from genomeai_api.schemas.search import (
    AdvancedFilterGroup,
    AdvancedFilterRule,
    CoordinateIntervalModel,
    CoordinateSearchRequest,
    DomainSearchRequest,
    FilterRule,
    FullTextSearchConfig,
    FullTextSearchRequest,
    PaginationRequest,
    SortRequest,
)
from genomeai_api.search.domain_search import (
    DATASET_SEARCH,
    DOMAIN_SEARCH_CONFIGS,
    EXPERIMENT_SEARCH,
    GENE_SEARCH,
    GENOME_SEARCH,
    PROJECT_SEARCH,
    PROTEIN_SEARCH,
    SAMPLE_SEARCH,
    STUDY_SEARCH,
    TRANSCRIPT_SEARCH,
    VARIANT_SEARCH,
    DomainSearchConfig,
)
from genomeai_api.services.search import SearchService
from pydantic import ValidationError


class TestDomainSearchConfigs:
    def test_all_domains_present(self) -> None:
        expected = {
            "gene", "protein", "variant", "transcript", "genome",
            "study", "sample", "dataset", "experiment", "project",
        }
        assert set(DOMAIN_SEARCH_CONFIGS.keys()) == expected

    def test_each_config_has_model(self) -> None:
        expected_models = {
            "gene": Gene,
            "protein": Protein,
            "variant": Variant,
            "transcript": Transcript,
            "genome": Genome,
            "study": Study,
            "sample": Sample,
            "dataset": Dataset,
            "experiment": Experiment,
            "project": Project,
        }
        for name, expected in expected_models.items():
            assert DOMAIN_SEARCH_CONFIGS[name].model is expected

    def test_each_config_has_search_fields(self) -> None:
        for name, config in DOMAIN_SEARCH_CONFIGS.items():
            assert len(config.search_fields) > 0, f"{name} has no search_fields"

    def test_each_config_has_fts_fields(self) -> None:
        for name, config in DOMAIN_SEARCH_CONFIGS.items():
            assert len(config.fts_fields) > 0, f"{name} has no fts_fields"

    def test_coordinate_domains(self) -> None:
        assert GENE_SEARCH.has_coordinate_search is True
        assert VARIANT_SEARCH.has_coordinate_search is True
        assert TRANSCRIPT_SEARCH.has_coordinate_search is True
        assert PROTEIN_SEARCH.has_coordinate_search is False
        assert GENOME_SEARCH.has_coordinate_search is False
        assert STUDY_SEARCH.has_coordinate_search is False
        assert SAMPLE_SEARCH.has_coordinate_search is False
        assert DATASET_SEARCH.has_coordinate_search is False
        assert EXPERIMENT_SEARCH.has_coordinate_search is False
        assert PROJECT_SEARCH.has_coordinate_search is False

    def test_variant_single_position_columns(self) -> None:
        assert VARIANT_SEARCH.coordinate_start_column == "position"
        assert VARIANT_SEARCH.coordinate_end_column == "position"

    def test_search_fields_are_mapped_columns(self) -> None:
        for name, config in DOMAIN_SEARCH_CONFIGS.items():
            for field in config.search_fields:
                assert hasattr(config.model, field), (
                    f"{name}.search_fields contains '{field}' "
                    f"but {config.model.__name__} has no such column"
                )

    def test_fts_fields_are_mapped_columns(self) -> None:
        for name, config in DOMAIN_SEARCH_CONFIGS.items():
            for field in config.fts_fields:
                assert hasattr(config.model, field), (
                    f"{name}.fts_fields contains '{field}' "
                    f"but {config.model.__name__} has no such column"
                )


class TestDomainSearchRequest:
    def test_defaults(self) -> None:
        req = DomainSearchRequest()
        assert req.q is None
        assert req.pagination.page == 1
        assert req.pagination.page_size == 20
        assert req.sort is None
        assert req.filters is None
        assert req.advanced_filters is None

    def test_with_q(self) -> None:
        req = DomainSearchRequest(q="BRCA1")
        assert req.q == "BRCA1"

    def test_with_pagination(self) -> None:
        req = DomainSearchRequest(
            q="test",
            pagination=PaginationRequest(page=2, page_size=10),
        )
        assert req.pagination.page == 2
        assert req.pagination.page_size == 10

    def test_with_sort(self) -> None:
        req = DomainSearchRequest(
            sort=SortRequest(sort_by="gene_name", sort_order="desc"),
        )
        assert req.sort is not None
        assert req.sort.sort_by == "gene_name"
        assert req.sort.sort_order == "desc"

    def test_with_filters(self) -> None:
        req = DomainSearchRequest(
            filters=[FilterRule(field="biotype", operator="equals", value="protein_coding")],
        )
        assert req.filters is not None
        assert len(req.filters) == 1

    def test_with_advanced_filters_simple(self) -> None:
        req = DomainSearchRequest(
            advanced_filters=AdvancedFilterGroup(
                children=[
                    AdvancedFilterRule(
                        field="biotype", operator="equals", value="protein_coding"
                    ),
                ],
            ),
        )
        assert req.advanced_filters is not None


class _MockSession:
    """Helper to create a mock async session with predictable query results."""

    @staticmethod
    def create(items: list[str], total: int = 0) -> AsyncMock:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = total if total else len(items)
        data_scalar = MagicMock()
        data_scalar.all.return_value = items
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar
        session.execute = AsyncMock(side_effect=[count_result, data_result])
        return session


class TestSearchServiceDomainSearch:
    @pytest.mark.asyncio
    async def test_gene_search(self) -> None:
        session = _MockSession.create(["g1", "g2"])
        service = SearchService(session)
        request = DomainSearchRequest(q="BRCA1")
        result = await service.domain_search(GENE_SEARCH, request)
        assert result.pagination.total_count == 2

    @pytest.mark.asyncio
    async def test_protein_search(self) -> None:
        session = _MockSession.create(["p1"])
        service = SearchService(session)
        request = DomainSearchRequest(q="kinase")
        result = await service.domain_search(PROTEIN_SEARCH, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_variant_search(self) -> None:
        session = _MockSession.create(["v1", "v2", "v3"])
        service = SearchService(session)
        request = DomainSearchRequest(q="rs123")
        result = await service.domain_search(VARIANT_SEARCH, request)
        assert result.pagination.total_count == 3

    @pytest.mark.asyncio
    async def test_transcript_search(self) -> None:
        session = _MockSession.create(["t1"])
        service = SearchService(session)
        request = DomainSearchRequest(q="NM_001")
        result = await service.domain_search(TRANSCRIPT_SEARCH, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_genome_search(self) -> None:
        session = _MockSession.create(["g1"])
        service = SearchService(session)
        request = DomainSearchRequest(q="GRCh38")
        result = await service.domain_search(GENOME_SEARCH, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_study_search(self) -> None:
        session = _MockSession.create(["s1"])
        service = SearchService(session)
        request = DomainSearchRequest(q="cancer")
        result = await service.domain_search(STUDY_SEARCH, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_sample_search(self) -> None:
        session = _MockSession.create(["s1", "s2"])
        service = SearchService(session)
        request = DomainSearchRequest(q="brain")
        result = await service.domain_search(SAMPLE_SEARCH, request)
        assert result.pagination.total_count == 2

    @pytest.mark.asyncio
    async def test_dataset_search(self) -> None:
        session = _MockSession.create(["d1"])
        service = SearchService(session)
        request = DomainSearchRequest(q="RNA-seq")
        result = await service.domain_search(DATASET_SEARCH, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_experiment_search(self) -> None:
        session = _MockSession.create(["e1"])
        service = SearchService(session)
        request = DomainSearchRequest(q="HiSeq")
        result = await service.domain_search(EXPERIMENT_SEARCH, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_project_search(self) -> None:
        session = _MockSession.create(["pr1", "pr2"])
        service = SearchService(session)
        request = DomainSearchRequest(q="ENCODE")
        result = await service.domain_search(PROJECT_SEARCH, request)
        assert result.pagination.total_count == 2

    @pytest.mark.asyncio
    async def test_search_without_q_returns_all(self) -> None:
        session = _MockSession.create(["g1", "g2", "g3"], total=3)
        service = SearchService(session)
        request = DomainSearchRequest()
        result = await service.domain_search(GENE_SEARCH, request)
        assert result.pagination.total_count == 3

    @pytest.mark.asyncio
    async def test_search_with_filters(self) -> None:
        session = _MockSession.create(["g1"])
        service = SearchService(session)
        request = DomainSearchRequest(
            q="BRCA",
            filters=[FilterRule(field="biotype", operator="equals", value="protein_coding")],
        )
        result = await service.domain_search(GENE_SEARCH, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_search_with_sort(self) -> None:
        session = _MockSession.create(["g1", "g2"])
        service = SearchService(session)
        request = DomainSearchRequest(
            sort=SortRequest(sort_by="gene_name", sort_order="asc"),
        )
        result = await service.domain_search(GENE_SEARCH, request)
        assert result.pagination.total_count == 2

    @pytest.mark.asyncio
    async def test_search_with_pagination(self) -> None:
        session = _MockSession.create(["g1"])
        service = SearchService(session)
        request = DomainSearchRequest(
            pagination=PaginationRequest(page=2, page_size=10),
        )
        result = await service.domain_search(GENE_SEARCH, request)
        assert result.pagination.page == 2
        assert result.pagination.page_size == 10

    @pytest.mark.asyncio
    async def test_search_empty_results(self) -> None:
        session = _MockSession.create([], total=0)
        service = SearchService(session)
        request = DomainSearchRequest(q="NONEXISTENT")
        result = await service.domain_search(GENE_SEARCH, request)
        assert result.pagination.total_count == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_search_invalid_field_filter(self) -> None:
        session = _MockSession.create([])
        service = SearchService(session)
        request = DomainSearchRequest(
            filters=[FilterRule(field="nonexistent_column", operator="equals", value="x")],
        )
        with pytest.raises(ValueError, match="Invalid filter field"):
            await service.domain_search(GENE_SEARCH, request)

    @pytest.mark.asyncio
    async def test_search_invalid_sort_field(self) -> None:
        session = _MockSession.create([])
        service = SearchService(session)
        request = DomainSearchRequest(
            sort=SortRequest(sort_by="nonexistent", sort_order="asc"),
        )
        with pytest.raises(ValueError, match="Invalid sort field"):
            await service.domain_search(GENE_SEARCH, request)

    @pytest.mark.asyncio
    async def test_search_with_advanced_filters(self) -> None:
        session = _MockSession.create(["g1"])
        service = SearchService(session)
        request = DomainSearchRequest(
            q="BRCA",
            advanced_filters=AdvancedFilterGroup(
                children=[
                    AdvancedFilterRule(
                        field="biotype", operator="equals", value="protein_coding"
                    ),
                ],
            ),
        )
        result = await service.domain_search(GENE_SEARCH, request)
        assert result.pagination.total_count == 1


class TestSearchServiceDomainFTS:
    @pytest.mark.asyncio
    async def test_gene_fts(self) -> None:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        mock_row = MagicMock()
        mock_row._mapping = {
            "genes": MagicMock(),
            "_rank": 0.5,
        }
        data_result = MagicMock()
        data_result.all.return_value = [mock_row, mock_row]
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = DomainSearchRequest()
        result = await service.domain_search_fts(GENE_SEARCH, request, fts_query="BRCA1")
        assert result.pagination.total_count == 2

    @pytest.mark.asyncio
    async def test_protein_fts(self) -> None:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_row = MagicMock()
        mock_row._mapping = {
            "proteins": MagicMock(),
            "_rank": 0.8,
        }
        data_result = MagicMock()
        data_result.all.return_value = [mock_row]
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = DomainSearchRequest()
        result = await service.domain_search_fts(PROTEIN_SEARCH, request, fts_query="kinase")
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_variant_fts(self) -> None:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 3
        mock_row = MagicMock()
        mock_row._mapping = {
            "variants": MagicMock(),
            "_rank": 0.6,
        }
        data_result = MagicMock()
        data_result.all.return_value = [mock_row, mock_row, mock_row]
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = DomainSearchRequest()
        result = await service.domain_search_fts(VARIANT_SEARCH, request, fts_query="rs123")
        assert result.pagination.total_count == 3

    @pytest.mark.asyncio
    async def test_fts_with_highlights(self) -> None:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_row = MagicMock()
        mock_row._mapping = {
            "genes": MagicMock(),
            "_rank": 0.9,
            "gene_name_highlight": "<b>BRCA</b>1",
            "description_highlight": "breast cancer",
        }
        data_result = MagicMock()
        data_result.all.return_value = [mock_row]
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = DomainSearchRequest()
        result = await service.domain_search_fts(GENE_SEARCH, request, fts_query="BRCA")
        assert result.pagination.total_count == 1
        assert result.highlights is not None
        assert len(result.highlights) == 1

    @pytest.mark.asyncio
    async def test_fts_empty_results(self) -> None:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        data_result = MagicMock()
        data_result.all.return_value = []
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = DomainSearchRequest()
        result = await service.domain_search_fts(GENE_SEARCH, request, fts_query="NONEXISTENT")
        assert result.pagination.total_count == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_fts_with_filters(self) -> None:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_row = MagicMock()
        mock_row._mapping = {
            "genes": MagicMock(),
            "_rank": 0.7,
        }
        data_result = MagicMock()
        data_result.all.return_value = [mock_row]
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = DomainSearchRequest(
            filters=[FilterRule(field="biotype", operator="equals", value="protein_coding")],
        )
        result = await service.domain_search_fts(GENE_SEARCH, request, fts_query="BRCA")
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_fts_with_q(self) -> None:
        session = AsyncMock(spec=["execute"])
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        mock_row = MagicMock()
        mock_row._mapping = {
            "genes": MagicMock(),
            "_rank": 0.7,
        }
        data_result = MagicMock()
        data_result.all.return_value = [mock_row]
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = DomainSearchRequest(q="BRCA")
        result = await service.domain_search_fts(GENE_SEARCH, request, fts_query="BRCA1")
        assert result.pagination.total_count == 1


class TestDomainCoordinateSearch:
    @pytest.mark.asyncio
    async def test_gene_coordinate_search(self) -> None:
        session = _MockSession.create(["g1"])
        service = SearchService(session)
        request = CoordinateSearchRequest(
            interval=CoordinateIntervalModel(chromosome="chr1", start=0, end=100000),
            match_type="overlap",
        )
        result = await service.coordinate_search(Gene, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_variant_coordinate_search(self) -> None:
        session = _MockSession.create(["v1"])
        service = SearchService(session)
        request = CoordinateSearchRequest(
            interval=CoordinateIntervalModel(chromosome="chr1", start=150, end=150),
            match_type="exact",
            start_column="position",
            end_column="position",
        )
        result = await service.coordinate_search(Variant, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_transcript_coordinate_search(self) -> None:
        session = _MockSession.create(["t1"])
        service = SearchService(session)
        request = CoordinateSearchRequest(
            interval=CoordinateIntervalModel(chromosome="chr1", start=0, end=100000),
            match_type="overlap",
        )
        result = await service.coordinate_search(Transcript, request)
        assert result.pagination.total_count == 1

    @pytest.mark.asyncio
    async def test_coordinate_search_empty(self) -> None:
        session = _MockSession.create([], total=0)
        service = SearchService(session)
        request = CoordinateSearchRequest(
            interval=CoordinateIntervalModel(chromosome="chrZ", start=0, end=100),
        )
        result = await service.coordinate_search(Gene, request)
        assert result.pagination.total_count == 0


class TestFullTextSearchRequest:
    def test_valid_request(self) -> None:
        req = FullTextSearchRequest(
            search=DomainSearchRequest(),
            fts=FullTextSearchConfig(
                query="BRCA1",
                columns=["gene_name", "description"],
            ),
        )
        assert req.fts.query == "BRCA1"

    def test_request_with_filters(self) -> None:
        req = FullTextSearchRequest(
            search=DomainSearchRequest(
                filters=[FilterRule(field="biotype", operator="equals", value="protein_coding")],
            ),
            fts=FullTextSearchConfig(
                query="BRCA1",
                columns=["gene_name", "description"],
            ),
        )
        assert req.search.filters is not None
        assert len(req.search.filters) == 1


class TestDomainSearchValidation:
    def test_domain_search_request_empty_q(self) -> None:
        req = DomainSearchRequest(q="")
        assert req.q == ""

    def test_domain_search_request_none_q(self) -> None:
        req = DomainSearchRequest(q=None)
        assert req.q is None

    def test_domain_search_request_invalid_filter(self) -> None:
        with pytest.raises(ValidationError):
            DomainSearchRequest(
                filters=[FilterRule(field="", operator="equals", value="x")],
            )

    def test_config_not_frozen(self) -> None:
        config = DomainSearchConfig(
            model=Gene,
            search_fields=["gene_name"],
            fts_fields=["gene_name"],
        )
        assert config.model is Gene
        assert config.search_fields == ["gene_name"]
