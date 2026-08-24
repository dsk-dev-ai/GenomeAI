from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.workflows.models import (
    StepRun,
    Workflow,
    WorkflowDependency,
    WorkflowRun,
    WorkflowStep,
)
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID


def _constraint_names(model: type) -> set[str]:
    return {c.name for c in model.__table__.constraints if c.name}


def test_all_workflow_models_inherit_base() -> None:
    for model in (Workflow, WorkflowStep, WorkflowDependency, WorkflowRun, StepRun):
        assert issubclass(model, Base)


def test_workflow_table_and_columns() -> None:
    assert Workflow.__tablename__ == "workflows"
    id_col = Workflow.__table__.columns["id"]
    assert isinstance(id_col.type, UUID)
    assert id_col.primary_key
    name_col = Workflow.__table__.columns["name"]
    assert name_col.nullable is False
    assert name_col.index is True
    assert Workflow.__table__.columns["description"].nullable is True
    version_col = Workflow.__table__.columns["version"]
    assert version_col.server_default.arg == "0.1.0"
    status_col = Workflow.__table__.columns["status"]
    assert status_col.server_default.arg == "draft"


def test_workflow_status_constrained_to_vocabulary() -> None:
    check = next(
        c
        for c in Workflow.__table__.constraints
        if getattr(c, "name", None) == "ck_workflow_status"
    )
    sql = str(check.sqltext)
    assert "'draft'" in sql
    assert "'active'" in sql
    assert "'archived'" in sql


def test_workflow_column_defaults() -> None:
    id_col = Workflow.__table__.columns["id"]
    assert id_col.default is not None and id_col.default.is_callable
    assert Workflow.__table__.columns["version"].default.arg == "0.1.0"
    assert Workflow.__table__.columns["status"].default.arg == "draft"
    wf = Workflow(name="w")
    # Relationship collections initialize eagerly; scalars populate at flush.
    assert wf.steps == []
    assert wf.dependencies == []
    assert wf.runs == []


def test_workflow_step_table_constraints() -> None:
    assert WorkflowStep.__tablename__ == "workflow_steps"
    assert "uq_workflow_step_name" in _constraint_names(WorkflowStep)
    assert "uq_workflow_step_scope" in _constraint_names(WorkflowStep)
    indexes = {ix.name for ix in WorkflowStep.__table__.indexes}
    assert "ix_workflow_steps_workflow_position" in indexes
    config_col = WorkflowStep.__table__.columns["configuration"]
    assert isinstance(config_col.type, JSONB)
    position_col = WorkflowStep.__table__.columns["position"]
    assert position_col.server_default.arg == "0"


def test_workflow_step_configuration_defaults_to_empty_dict() -> None:
    config_col = WorkflowStep.__table__.columns["configuration"]
    assert config_col.default is not None and config_col.default.is_callable
    assert config_col.default.arg.__name__ == "dict"
    position_col = WorkflowStep.__table__.columns["position"]
    assert position_col.default is not None
    assert position_col.default.arg == 0
    # Explicit configuration passes through untouched.
    step = WorkflowStep(
        workflow_id=uuid.uuid4(), name="s", step_type="noop", configuration={"k": 1}
    )
    assert step.configuration == {"k": 1}


def test_workflow_dependency_table_constraints() -> None:
    assert WorkflowDependency.__tablename__ == "workflow_dependencies"
    names = _constraint_names(WorkflowDependency)
    assert "uq_workflow_dependency_edge" in names
    assert "ck_workflow_dependency_not_self" in names
    # Both endpoints are workflow-scoped via composite FKs into
    # workflow_steps(workflow_id, id) — cross-workflow edges are impossible.
    fk_constraints = {
        c.name: c
        for c in WorkflowDependency.__table__.constraints
        if isinstance(c, ForeignKeyConstraint)
    }
    assert set(fk_constraints) == {
        "fk_workflow_dependency_from_step",
        "fk_workflow_dependency_to_step",
        None,  # unnamed single-column FK: workflow_id -> workflows.id
    }
    parent_fk = fk_constraints[None]
    assert [fk.target_fullname for fk in parent_fk.elements] == ["workflows.id"]
    expected_pairs = {
        "fk_workflow_dependency_from_step": ["workflow_id", "from_step_id"],
        "fk_workflow_dependency_to_step": ["workflow_id", "to_step_id"],
    }
    for name, fk in fk_constraints.items():
        if name not in expected_pairs:
            continue
        assert [col.name for col in fk.columns] == expected_pairs[name]
        assert [elem.target_fullname for elem in fk.elements] == [
            "workflow_steps.workflow_id",
            "workflow_steps.id",
        ]
        assert fk.ondelete == "CASCADE"


def test_workflow_run_state_defaults() -> None:
    assert WorkflowRun.__tablename__ == "workflow_runs"
    state_col = WorkflowRun.__table__.columns["state"]
    assert state_col.server_default.arg == "pending"
    assert state_col.nullable is False
    assert WorkflowRun.__table__.columns["started_at"].nullable is True
    assert WorkflowRun.__table__.columns["finished_at"].nullable is True
    run = WorkflowRun(workflow_id=uuid.uuid4())
    assert run.started_at is None
    assert run.finished_at is None
    assert run.step_runs == []


def test_workflow_run_composite_index() -> None:
    indexes = {ix.name for ix in WorkflowRun.__table__.indexes}
    assert "ix_workflow_runs_workflow_state" in indexes


def test_step_run_table_constraints() -> None:
    assert StepRun.__tablename__ == "workflow_step_runs"
    names = _constraint_names(StepRun)
    assert "uq_workflow_step_run" in names
    indexes = {ix.name for ix in StepRun.__table__.indexes}
    assert "ix_workflow_step_runs_run_state" in indexes
    fks = StepRun.__table__.foreign_keys
    assert {fk.target_fullname for fk in fks} == {
        "workflow_runs.id",
        "workflow_steps.id",
    }
    run = StepRun(run_id=uuid.uuid4(), step_id=uuid.uuid4())
    state_col = StepRun.__table__.columns["state"]
    assert state_col.server_default.arg == "pending"
    assert run.started_at is None
    assert run.finished_at is None
    position_col = StepRun.__table__.columns["position"]
    assert position_col.server_default.arg == "0"
    assert position_col.nullable is False


def test_relationships_wire_parent_children_via_back_populates() -> None:
    wf = Workflow(name="pipeline")
    step_a = WorkflowStep(id=uuid.uuid4(), workflow_id=wf.id, name="A", step_type="t")
    step_b = WorkflowStep(id=uuid.uuid4(), workflow_id=wf.id, name="B", step_type="t")
    dep = WorkflowDependency(
        workflow_id=wf.id, from_step_id=step_a.id, to_step_id=step_b.id
    )
    run = WorkflowRun(workflow_id=wf.id)
    step_run = StepRun(run_id=run.id, step_id=step_a.id)

    wf.steps.extend([step_a, step_b])
    wf.dependencies.append(dep)
    wf.runs.append(run)
    run.step_runs.append(step_run)
    # Many-to-one endpoints are assigned explicitly (resolved at flush/ORM level).
    dep.from_step = step_a
    dep.to_step = step_b
    step_run.step = step_a

    assert step_a.workflow is wf
    assert dep.workflow is wf
    assert dep.from_step is step_a
    assert dep.to_step is step_b
    assert run.workflow is wf
    assert step_run.run is run
    assert step_run.step is step_a
    assert step_a.as_source_dependencies == [dep]
    assert step_b.as_target_dependencies == [dep]
    assert len(wf.steps) == 2
