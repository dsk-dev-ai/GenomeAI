"""Shared enums and identifiers for the Data Integration Foundation (Phase 7 base).

This module defines strongly-typed vocabulary shared by the connector layer,
the persistence layer, and the internal admin API. Values are stored as their
lowercase string values in PostgreSQL.
"""

from __future__ import annotations

from enum import StrEnum


class SourceType(StrEnum):
    """Category of data a source provides (mirrors the External Data master plan)."""

    GENOME = "genome"
    GENE = "gene"
    VARIANT = "variant"
    PROTEIN = "protein"
    EXPRESSION = "expression"
    PHENOTYPE = "phenotype"
    PATHWAY = "pathway"
    LITERATURE = "literature"
    CHEMICAL = "chemical"
    OTHER = "other"


class AccessMode(StrEnum):
    """How GenomeAI accesses the source (External Data master plan §18)."""

    LIVE = "live"
    CACHED = "cached"
    INGESTED = "ingested"
    BULK = "bulk"


class AuthMode(StrEnum):
    """Authentication modes a connector may require."""

    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"


class SyncStatus(StrEnum):
    """Synchronization lifecycle of a data source."""

    UNKNOWN = "unknown"
    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobState(StrEnum):
    """Lightweight ingestion-job state machine (Phase 7 foundation)."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EntityType(StrEnum):
    """Canonical GenomeAI entity kinds that external identifiers may map to.

    The list mirrors the canonical entities documented in the External Data
    master plan (§12). It is deliberately conservative: existing database
    entities plus the documented planned canonical entities.
    """

    GENOME = "genome"
    ASSEMBLY = "assembly"
    CHROMOSOME = "chromosome"
    GENE = "gene"
    TRANSCRIPT = "transcript"
    PROTEIN = "protein"
    VARIANT = "variant"
    SAMPLE = "sample"
    EXPERIMENT = "experiment"
    DATASET = "dataset"
    STUDY = "study"
    PROJECT = "project"
    DISEASE = "disease"
    PHENOTYPE = "phenotype"
    DRUG = "drug"
    PUBLICATION = "publication"


# Allowed job-state transitions. Each value lists the states it may move to.
JOB_STATE_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.PENDING: frozenset({JobState.RUNNING, JobState.CANCELLED}),
    JobState.RUNNING: frozenset({JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}),
    JobState.SUCCEEDED: frozenset(),
    JobState.FAILED: frozenset(),
    JobState.CANCELLED: frozenset(),
}

def can_transition(current: JobState, next_state: JobState) -> bool:
    """Whether an ingestion job may move from `current` to `next_state`."""
    return next_state in JOB_STATE_TRANSITIONS.get(current, frozenset())


__all__ = [
    "AccessMode",
    "AuthMode",
    "EntityType",
    "JOB_STATE_TRANSITIONS",
    "JobState",
    "SourceType",
    "SyncStatus",
    "can_transition",
]
