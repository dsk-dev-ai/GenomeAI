from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest


@pytest.fixture
def migration() -> object:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    for path in versions_dir.iterdir():
        if path.name.endswith(".py") and "c5e1a7b9d3f2" in path.name:
            spec = util.spec_from_file_location("workflow_migration", path)
            assert spec is not None
            mod = util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
    msg = "migration c5e1a7b9d3f2 not found"
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
    assert migration.down_revision == "b3d9f6a1c2e4"  # type: ignore[union-attr]


def test_migration_creates_all_workflow_tables(migration: object) -> None:
    source = Path(
        migration.__file__  # type: ignore[attr-defined]
    ).read_text(encoding="utf-8")
    for table in (
        '"workflows"',
        '"workflow_steps"',
        '"workflow_dependencies"',
        '"workflow_runs"',
        '"workflow_step_runs"',
    ):
        assert table in source


def test_migration_declares_dag_safety_constraints(migration: object) -> None:
    source = Path(
        migration.__file__  # type: ignore[attr-defined]
    ).read_text(encoding="utf-8")
    for constraint in (
        "uq_workflow_step_name",
        "uq_workflow_dependency_edge",
        "ck_workflow_dependency_not_self",
        "uq_workflow_step_run",
    ):
        assert constraint in source
