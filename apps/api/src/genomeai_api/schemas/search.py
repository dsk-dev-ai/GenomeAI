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
