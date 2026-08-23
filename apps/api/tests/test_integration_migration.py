from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest


@pytest.fixture
def migration() -> object:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    for path in versions_dir.iterdir():
        if path.name.endswith(".py") and "b3d9f6a1c2e4" in path.name:
            spec = util.spec_from_file_location("integration_migration", path)
            assert spec is not None
            mod = util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
    msg = "migration b3d9f6a1c2e4 not found"
    raise AssertionError(msg)


def test_migration_upgrade_callable(migration: object) -> None:
    assert callable(migration.upgrade)  # type: ignore[union-attr]


def test_migration_downgrade_callable(migration: object) -> None:
    assert callable(migration.downgrade)  # type: ignore[union-attr]


def test_migration_revision_present(migration: object) -> None:
    rev: str = migration.revision  # type: ignore[union-attr]
    assert isinstance(rev, str)
    assert len(rev) >= 8


def test_migration_chains_to_previous_head(migration: object) -> None:
    assert migration.down_revision == "7cf6d6506732"  # type: ignore[union-attr]


def test_migration_creates_all_foundation_tables(migration: object) -> None:
    source = Path(
        migration.__file__  # type: ignore[attr-defined]
    ).read_text(encoding="utf-8")
    for table in (
        '"data_sources"',
        '"external_identifiers"',
        '"provenance"',
        '"ingestion_jobs"',
    ):
        assert table in source
