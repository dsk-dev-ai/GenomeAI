from __future__ import annotations

from importlib import util
from pathlib import Path


def _find_migration_file() -> Path:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    for path in versions_dir.iterdir():
        if path.name.endswith(".py") and not path.name.startswith("__"):
            content = path.read_text()
            if "0f3f64decdb7" in content and "genomes" in content:
                return path
    msg = "migration for genomes table not found"
    raise AssertionError(msg)


def test_migration_file_exists() -> None:
    path = _find_migration_file()
    assert path.exists()


def test_migration_imports() -> None:
    path = _find_migration_file()
    spec = util.spec_from_file_location("genome_migration", path)
    assert spec is not None
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


def test_migration_revision_id() -> None:
    path = _find_migration_file()
    spec = util.spec_from_file_location("genome_migration", path)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    assert mod.down_revision == "6ca189ad6980"
    assert mod.revision is not None
    assert len(mod.revision) >= 8


def test_migration_references_genomes_table() -> None:
    path = _find_migration_file()
    content = path.read_text()
    assert "genomes" in content


def test_migration_has_downgrade() -> None:
    path = _find_migration_file()
    content = path.read_text()
    assert "drop_table(\"genomes\")" in content or "drop_table('genomes')" in content
