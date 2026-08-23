from __future__ import annotations

import uuid

import pytest
from genomeai_api.schemas.integration import (
    DataSourceCreate,
    ExternalIdentifierCreate,
    IngestionJobComplete,
    IngestionJobCreate,
    IngestionJobFailure,
)
from pydantic import ValidationError


def test_valid_source_create() -> None:
    data = DataSourceCreate(
        source_id="genomeai-reference",
        provider="GenomeAI",
        display_name="Reference",
        api_base_url="https://reference.internal",
    )
    assert data.enabled is True
    assert data.auth_mode == "none"


@pytest.mark.parametrize("url", ["ftp://x", "not-a-url", "javascript:alert(1)", ""])
def test_source_create_rejects_unsafe_schemes(url: str) -> None:
    with pytest.raises(ValidationError):
        DataSourceCreate(
            source_id="s",
            provider="p",
            display_name="d",
            api_base_url=url,
        )


def test_source_create_rejects_bad_source_id() -> None:
    with pytest.raises(ValidationError):
        DataSourceCreate(
            source_id="Bad Id!",
            provider="p",
            display_name="d",
            api_base_url="https://ok.example.com",
        )


def test_identifier_requires_known_entity_type() -> None:
    with pytest.raises(ValidationError):
        ExternalIdentifierCreate(
            source_id="s",
            external_id="X:1",
            entity_type="not-an-entity",
            genomeai_entity_id=uuid.uuid4(),
        )


def test_job_create_requires_source() -> None:
    with pytest.raises(ValidationError):
        IngestionJobCreate(source_id="")


def test_job_complete_counts_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        IngestionJobComplete(received=-1, succeeded=0)


def test_job_failure_requires_message() -> None:
    with pytest.raises(ValidationError):
        IngestionJobFailure(received=1, failed=1, error_message="")
