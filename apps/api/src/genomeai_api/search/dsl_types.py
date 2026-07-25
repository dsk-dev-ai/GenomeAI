from __future__ import annotations

from pydantic import BaseModel, Field

from genomeai_api.schemas.search import (
    FilterRule,
    PaginationRequest,
    SortRequest,
)


class DslSearchQuery(BaseModel):
    where: dict[str, object] = Field(
        default_factory=dict,
        description="DSL query structure with and/or/not and field conditions",
    )
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)
    sort: SortRequest | None = None
    filters: list[FilterRule] | None = None
