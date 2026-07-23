from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

FilterOperator = Literal[
    "equals",
    "contains",
    "starts_with",
    "ends_with",
    "in",
    "is_null",
]

SortOrder = Literal["asc", "desc"]

QueryType = Literal["plain", "phrase", "websearch", "raw"]
WeightType = Literal["A", "B", "C", "D"]


class PaginationRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class SortRequest(BaseModel):
    sort_by: str = Field(min_length=1)
    sort_order: SortOrder = "asc"


class FilterRule(BaseModel):
    field: str = Field(min_length=1)
    operator: FilterOperator
    value: Any = None

    @model_validator(mode="after")
    def validate_is_null_value(self) -> FilterRule:
        if self.operator == "is_null" and not isinstance(self.value, bool):
            raise ValueError("Value for 'is_null' operator must be true or false")
        return self


class SearchRequest(BaseModel):
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)
    sort: SortRequest | None = None
    filters: list[FilterRule] | None = None

    @model_validator(mode="before")
    @classmethod
    def coerce_pagination(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "pagination" not in data or data["pagination"] is None:
                data["pagination"] = {}
        return data


class SearchResponse(BaseModel):
    items: list[Any]
    pagination: PaginationResponse


class FullTextSearchConfig(BaseModel):
    query: str = Field(min_length=1)
    config: str = "english"
    query_type: QueryType = "plain"
    columns: list[str] = Field(min_length=1)
    weights: list[WeightType] | None = None

    @model_validator(mode="after")
    def reject_whitespace_query(self) -> FullTextSearchConfig:
        if not self.query.strip():
            raise ValueError("Search query must not be whitespace-only")
        return self

    @model_validator(mode="after")
    def validate_weights_arity(self) -> FullTextSearchConfig:
        if self.weights is not None and len(self.weights) != len(self.columns):
            msg = (
                f"Number of weights ({len(self.weights)}) must match"
                f" number of columns ({len(self.columns)})"
            )
            raise ValueError(msg)
        return self


class FullTextSearchRequest(BaseModel):
    search: SearchRequest
    fts: FullTextSearchConfig


class HighlightedMatch(BaseModel):
    field: str
    snippet: str


class RankedSearchResult(BaseModel):
    rank: float
    highlights: list[HighlightedMatch] | None = None


class FullTextSearchResponse(BaseModel):
    items: list[Any]
    pagination: PaginationResponse
    ranks: list[float] | None = None
    highlights: list[list[HighlightedMatch]] | None = None
