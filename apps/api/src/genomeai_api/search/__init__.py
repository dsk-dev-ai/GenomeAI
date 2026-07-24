from genomeai_api.search.autocomplete import (
    build_prefix_query,
)
from genomeai_api.search.cache import (
    MemoryCache,
    NullCache,
    SuggestionCache,
    SuggestionCacheEntry,
    suggestion_cache_key,
)
from genomeai_api.search.coordinate_intervals import (
    apply_coordinate_filter,
)
from genomeai_api.search.coordinate_types import (
    CoordinateInterval,
    CoordinateMatchType,
)
from genomeai_api.search.coordinate_validation import (
    SUPPORTED_COORDINATE_MATCH_TYPES,
    validate_chromosome,
    validate_coordinate,
    validate_coordinate_request,
    validate_interval,
    validate_match_type,
)
from genomeai_api.search.expressions import (
    GroupExpression,
    LeafExpression,
    count_expressions,
    max_depth,
)
from genomeai_api.search.fts import (
    build_tsquery,
    build_tsvector,
)
from genomeai_api.search.highlighting import (
    apply_ts_headlines,
    build_ts_headline,
)
from genomeai_api.search.indexes import (
    create_gin_index,
    create_tsvector_column,
    create_tsvector_index,
)
from genomeai_api.search.operators import (
    ALL_OPERATORS,
    COMPARISON_OPERATORS,
    NULL_OPERATORS,
    OPERATORS_REQUIRING_LIST,
    OPERATORS_REQUIRING_NO_VALUE,
    RANGE_OPERATORS,
    SET_OPERATORS,
    STRING_OPERATORS,
    Operator,
)
from genomeai_api.search.query import (
    apply_fts_filter,
    apply_fts_to_statement,
)
from genomeai_api.search.query_builder import (
    build_clause,
)
from genomeai_api.search.ranking import (
    apply_ts_rank,
    apply_ts_rank_cd,
    order_by_rank_desc,
)
from genomeai_api.search.suggestions import (
    Suggestion,
    SuggestionMatchType,
    rank_suggestions,
)
from genomeai_api.search.validation import (
    MAX_EXPRESSIONS,
    MAX_RECURSION_DEPTH,
    ValidationError,
    validate_expression,
    validate_field_name,
    validate_operator_value,
)

__all__ = [
    "ALL_OPERATORS",
    "apply_coordinate_filter",
    "apply_fts_filter",
    "apply_fts_to_statement",
    "apply_ts_headlines",
    "apply_ts_rank",
    "apply_ts_rank_cd",
    "build_clause",
    "build_prefix_query",
    "build_ts_headline",
    "build_tsquery",
    "build_tsvector",
    "COMPARISON_OPERATORS",
    "CoordinateInterval",
    "CoordinateMatchType",
    "count_expressions",
    "create_gin_index",
    "create_tsvector_column",
    "create_tsvector_index",
    "GroupExpression",
    "LeafExpression",
    "MAX_EXPRESSIONS",
    "MAX_RECURSION_DEPTH",
    "max_depth",
    "MemoryCache",
    "NULL_OPERATORS",
    "NullCache",
    "OPERATORS_REQUIRING_LIST",
    "OPERATORS_REQUIRING_NO_VALUE",
    "Operator",
    "order_by_rank_desc",
    "RANGE_OPERATORS",
    "SET_OPERATORS",
    "STRING_OPERATORS",
    "SUPPORTED_COORDINATE_MATCH_TYPES",
    "Suggestion",
    "SuggestionCache",
    "SuggestionCacheEntry",
    "SuggestionMatchType",
    "suggestion_cache_key",
    "rank_suggestions",
    "validate_chromosome",
    "validate_coordinate",
    "validate_coordinate_request",
    "validate_expression",
    "validate_field_name",
    "validate_interval",
    "validate_match_type",
    "validate_operator_value",
    "ValidationError",
]
