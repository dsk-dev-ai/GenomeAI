from __future__ import annotations

import ast
import inspect
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


@pytest.fixture
def execution_migration() -> object:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    for path in versions_dir.iterdir():
        if path.name.endswith(".py") and "e8b2c4d6f9a3" in path.name:
            spec = util.spec_from_file_location("execution_migration", path)
            assert spec is not None
            mod = util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
    msg = "migration e8b2c4d6f9a3 not found"
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
        "uq_workflow_step_scope",
        "uq_workflow_dependency_edge",
        "ck_workflow_dependency_not_self",
        "ck_workflow_status",
        "uq_workflow_step_run",
        "fk_workflow_dependency_from_step",
        "fk_workflow_dependency_to_step",
    ):
        assert constraint in source


# --- Structural execution checks (DB-free) ---------------------------------
#
# These parse the migration's AST and verify that upgrade()/downgrade() are
# internally consistent: every created table is dropped in reverse order, and
# no foreign key references a table that has not been created yet. Live
# upgrade → downgrade → upgrade execution against PostgreSQL is additionally
# performed as part of the milestone validation procedure.

_MIGRATION_TABLES = (
    "workflows",
    "workflow_steps",
    "workflow_dependencies",
    "workflow_runs",
    "workflow_step_runs",
)


def _upgrade_statements(migration: object) -> list[tuple[str, object]]:
    """Returns (op_method, call_node) pairs from upgrade(), in source order."""

    source = Path(
        migration.__file__  # type: ignore[attr-defined]
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            statements: list[tuple[str, object]] = []
            for stmt in ast.walk(node):
                if (
                    isinstance(stmt, ast.Call)
                    and isinstance(stmt.func, ast.Attribute)
                ):
                    statements.append((stmt.func.attr, stmt))
            return statements
    msg = "no upgrade function found"
    raise AssertionError(msg)


def _constant_args(call: object) -> list[str]:
    return [
        arg.value
        for arg in getattr(call, "args", [])  # type: ignore[attr-defined]
        if isinstance(arg, ast.Constant)  # type: ignore[name-defined]
    ]


def _referenced_tables(call: object) -> set[str]:
    """Parent tables named in a ForeignKeyConstraint('col', ['t.c', ...]) call."""
    tables: set[str] = set()
    args = getattr(call, "args", [])
    for arg in args:
        if not isinstance(arg, ast.List):
            continue
        for element in arg.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                if "." in element.value:
                    tables.add(element.value.split(".", maxsplit=1)[0])
    return tables


def test_migration_upgrade_downgrade_are_symmetric(migration: object) -> None:
    created = [
        args[0]
        for method, call in _upgrade_statements(migration)
        if method == "create_table"
        for args in [_constant_args(call)]
        if args
    ]


    source = Path(
        migration.__file__  # type: ignore[attr-defined]
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    dropped: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
            for stmt in ast.walk(node):
                if (
                    isinstance(stmt, ast.Call)
                    and isinstance(stmt.func, ast.Attribute)
                    and stmt.func.attr == "drop_table"
                ):
                    names = [
                        arg.value for arg in stmt.args if isinstance(arg, ast.Constant)
                    ]
                    if names:
                        dropped.append(names[0])

    assert set(created) == set(dropped)
    assert len(created) == len(set(created)), "duplicate create_table"
    assert dropped == list(reversed(created)), "downgrade must reverse creation order"


def test_migration_fk_targets_exist_before_use(migration: object) -> None:
    known = set(_MIGRATION_TABLES)
    created: set[str] = set()
    for method, call in _upgrade_statements(migration):
        if method == "create_table":
            names = _constant_args(call)
            assert names, "create_table requires a name"
            created.add(names[0])
        elif method == "ForeignKeyConstraint":
            referenced = _referenced_tables(call)
            missing = referenced - created
            assert not missing, f"FK references table(s) not yet created: {missing}"
    # Sanity: the migration actually creates the full foundation schema.
    assert created == known


def test_execution_migration_chains_to_foundation_head(
    execution_migration: object,
) -> None:
    rev: str = execution_migration.revision  # type: ignore[union-attr]
    assert rev == "e8b2c4d6f9a3"
    assert execution_migration.down_revision == "c5e1a7b9d3f2"  # type: ignore[union-attr]


def _column_ops(migration: object, direction: str) -> list[tuple[str, str]]:
    source = inspect.getsource(
        migration.upgrade if direction == "upgrade" else migration.downgrade  # type: ignore[union-attr]
    )
    tree = ast.parse(source)
    ops: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in ("add_column", "drop_column"):
            continue
        table = ast.literal_eval(node.args[0])
        column_arg = node.args[1]
        if isinstance(column_arg, ast.Constant):
            column = column_arg.value
        else:
            assert isinstance(column_arg, ast.Call) and column_arg.args
            column = ast.literal_eval(column_arg.args[0])
        ops.append((direction, f"{table}.{column}"))
    return ops


def test_execution_migration_adds_result_columns(execution_migration: object) -> None:
    upgrades = _column_ops(execution_migration, "upgrade")

    assert ("upgrade", "workflow_step_runs.output") in upgrades
    assert ("upgrade", "workflow_step_runs.error_message") in upgrades
    assert len(upgrades) == 2


def test_execution_migration_is_symmetric(execution_migration: object) -> None:
    upgrades = {target for _, target in _column_ops(execution_migration, "upgrade")}
    downgrades = {
        target for _, target in _column_ops(execution_migration, "downgrade")
    }

    assert upgrades and downgrades == upgrades


def test_execution_migration_upgrade_callable(execution_migration: object) -> None:
    assert callable(execution_migration.upgrade)  # type: ignore[union-attr]


def test_execution_migration_downgrade_callable(execution_migration: object) -> None:
    assert callable(execution_migration.downgrade)  # type: ignore[union-attr]


@pytest.fixture
def scheduler_migration() -> object:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    for path in versions_dir.iterdir():
        if path.name.endswith(".py") and "f4b8d1c6e2a7" in path.name:
            spec = util.spec_from_file_location("scheduler_migration", path)
            assert spec is not None
            mod = util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
    msg = "migration f4b8d1c6e2a7 not found"
    raise AssertionError(msg)


def test_scheduler_migration_chains_to_execution_head(
    scheduler_migration: object,
) -> None:
    rev: str = scheduler_migration.revision  # type: ignore[union-attr]
    assert rev == "f4b8d1c6e2a7"
    assert scheduler_migration.down_revision == "e8b2c4d6f9a3"  # type: ignore[union-attr]


def test_scheduler_migration_creates_schedules_table(
    scheduler_migration: object,
) -> None:
    source = inspect.getsource(scheduler_migration.upgrade)  # type: ignore[union-attr]
    tree = ast.parse(source)

    tables = [
        ast.literal_eval(call.args[0])
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "create_table"
        and call.args
        and isinstance(call.args[0], ast.Constant)
    ]

    assert tables == ["workflow_schedules"]


def test_scheduler_migration_declares_lifecycle_constraints(
    scheduler_migration: object,
) -> None:
    source = inspect.getsource(scheduler_migration.upgrade)  # type: ignore[union-attr]

    assert '"ck_schedule_type"' in source or "'ck_schedule_type'" in source
    assert '"ck_schedule_state"' in source or "'ck_schedule_state'" in source
    assert (
        '"ck_schedule_shape_matches_type"' in source
        or "'ck_schedule_shape_matches_type'" in source
    )


def test_scheduler_migration_annotates_workflow_runs(
    scheduler_migration: object,
) -> None:
    mapping = {
        target.split(".", 1)[1]: target.split(".", 1)[0]
        for _, target in _column_ops(scheduler_migration, "upgrade")
    }

    assert mapping["schedule_id"] == "workflow_runs"
    assert mapping["scheduled_for"] == "workflow_runs"


def test_scheduler_migration_creates_occurrence_unique_index(
    scheduler_migration: object,
) -> None:
    source = inspect.getsource(scheduler_migration.upgrade)  # type: ignore[union-attr]

    assert "uq_workflow_runs_schedule_occurrence" in source
    assert "postgresql_where" in source


def test_scheduler_migration_is_symmetric(scheduler_migration: object) -> None:
    upgrade_src = inspect.getsource(scheduler_migration.upgrade)  # type: ignore[union-attr]
    downgrade_src = inspect.getsource(scheduler_migration.downgrade)  # type: ignore[union-attr]
    up_tree = ast.parse(upgrade_src)
    down_tree = ast.parse(downgrade_src)

    def _ops(tree: ast.AST) -> list[tuple[str, str]]:
        ops = []
        for call in ast.walk(tree):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                if call.func.attr in ("create_table", "drop_table"):
                    ops.append(("table", str(ast.literal_eval(call.args[0]))))
                elif call.func.attr == "create_index":
                    ops.append(("index", str(ast.literal_eval(call.args[0]))))
                elif call.func.attr == "drop_index":
                    ops.append(("index", str(ast.literal_eval(call.args[0]))))
                elif call.func.attr == "add_column":
                    column_arg = call.args[1]
                    column = (
                        ast.literal_eval(column_arg.args[0])
                        if isinstance(column_arg, ast.Call)
                        else ast.literal_eval(column_arg)
                    )
                    ops.append(("column", f"{ast.literal_eval(call.args[0])}.{column}"))
                elif call.func.attr == "drop_column":
                    table = ast.literal_eval(call.args[0])
                    column = ast.literal_eval(call.args[1])
                    ops.append(("column", f"{table}.{column}"))
        return ops

    up_ops = _ops(up_tree)
    down_ops = [(kind, target) for kind, target in reversed(_ops(down_tree))]

    assert up_ops and down_ops == up_ops


def test_scheduler_migration_fk_targets_exist_before_use(
    scheduler_migration: object,
) -> None:
    source = inspect.getsource(scheduler_migration.upgrade)  # type: ignore[union-attr]
    positions = {
        marker: source.find(marker)
        for marker in (
            'op.create_table(\n        "workflow_schedules"',
            '"schedule_id"',
        )
    }

    assert all(position >= 0 for position in positions.values())
    assert positions['op.create_table(\n        "workflow_schedules"'] < positions[
        '"schedule_id"'
    ]
