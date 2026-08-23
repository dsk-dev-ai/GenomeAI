"""Normalization boundary: raw records → canonical entities."""

from genomeai_api.integration.normalizers.base import (
    NormalizedEntity,
    Normalizer,
    ValidationIssue,
)

__all__ = ["NormalizedEntity", "Normalizer", "ValidationIssue"]
