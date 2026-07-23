from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest


@pytest.fixture
def migration() -> object:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    for path in versions_dir.iterdir():
        if path.name.endswith(".py") and "2325f8c4566c" in path.name:
            spec = util.spec_from_file_location("experiment_migration", path)
            assert spec is not None
            mod = util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
    msg = "migration 2325f8c4566c not found"
    raise AssertionError(msg)


def test_migration_upgrade_callable(migration: object) -> None:
    assert callable(migration.upgrade)  # type: ignore[union-attr]


def test_migration_downgrade_callable(migration: object) -> None:
    assert callable(migration.downgrade)  # type: ignore[union-attr]


def test_migration_revision_present(migration: object) -> None:
    rev: str = migration.revision  # type: ignore[union-attr]
    assert isinstance(rev, str)
    assert len(rev) >= 8


def test_migration_down_revision(migration: object) -> None:
    assert migration.down_revision == "cc42f7960492"  # type: ignore[union-attr]
