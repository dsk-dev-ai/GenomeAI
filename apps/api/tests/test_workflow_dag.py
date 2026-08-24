from __future__ import annotations

import pytest
from genomeai_api.workflows.dag import topological_order, validate_graph


def _codes(issues: list) -> list[str]:
    return [issue.code for issue in issues]


def test_valid_linear_dag_has_no_issues() -> None:
    issues = validate_graph(
        ["A", "B", "C"],
        [("A", "B"), ("B", "C")],
    )
    assert issues == []


def test_valid_branching_dag_has_no_issues() -> None:
    assert validate_graph(["A", "B", "C"], [("A", "B"), ("A", "C")]) == []


def test_valid_joining_dag_has_no_issues() -> None:
    assert validate_graph(["A", "B", "C"], [("A", "C"), ("B", "C")]) == []


def test_empty_workflow_is_rejected() -> None:
    issues = validate_graph([], [])
    assert _codes(issues) == ["empty-workflow"]


def test_duplicate_step_names_are_rejected() -> None:
    issues = validate_graph(["A", "B", "A"], [])
    assert _codes(issues) == ["duplicate-step"]
    assert "A" in issues[0].message


def test_self_dependency_is_rejected() -> None:
    issues = validate_graph(["A"], [("A", "A")])
    assert _codes(issues) == ["self-dependency"]


def test_missing_source_step_is_rejected() -> None:
    issues = validate_graph(["B"], [("A", "B")])
    assert _codes(issues) == ["missing-step"]
    assert "'A'" in issues[0].message


def test_missing_target_step_is_rejected() -> None:
    issues = validate_graph(["A"], [("A", "Z")])
    assert _codes(issues) == ["missing-step"]
    assert "'Z'" in issues[0].message


def test_duplicate_dependency_edge_is_rejected() -> None:
    issues = validate_graph(["A", "B"], [("A", "B"), ("A", "B")])
    assert _codes(issues) == ["duplicate-dependency"]


def test_two_node_cycle_is_detected() -> None:
    issues = validate_graph(["A", "B"], [("A", "B"), ("B", "A")])
    assert _codes(issues) == ["cycle"]
    assert "A" in issues[0].message and "B" in issues[0].message


def test_three_node_cycle_is_detected() -> None:
    issues = validate_graph(
        ["A", "B", "C"],
        [("A", "B"), ("B", "C"), ("C", "A")],
    )
    assert _codes(issues) == ["cycle"]


def test_cycle_with_valid_tail_still_detected() -> None:
    # D → A, and A ⇄ B form a cycle; D itself is fine but the graph is not.
    issues = validate_graph(
        ["A", "B", "D"],
        [("D", "A"), ("A", "B"), ("B", "A")],
    )
    assert _codes(issues) == ["cycle"]


def test_validation_reports_multiple_issues_deterministically() -> None:
    first = validate_graph(["A", "A"], [("A", "A"), ("X", "A")])
    second = validate_graph(["A", "A"], [("A", "A"), ("X", "A")])
    assert first == second
    assert set(_codes(first)) == {"duplicate-step", "self-dependency", "missing-step"}


def test_topological_order_linear() -> None:
    assert topological_order(["C", "A", "B"], [("A", "B"), ("B", "C")]) == [
        "A",
        "B",
        "C",
    ]


def test_topological_order_lexicographic_tie_break() -> None:
    # B and C are both ready after A; B must come first deterministically.
    order = topological_order(["C", "B", "A"], [("A", "B"), ("A", "C")])
    assert order == ["A", "B", "C"]


def test_topological_order_independent_steps_sorted() -> None:
    assert topological_order(["zeta", "alpha"], []) == ["alpha", "zeta"]


def test_topological_order_joins_respect_all_predecessors() -> None:
    order = topological_order(["A", "B", "C"], [("A", "C"), ("B", "C")])
    assert order.index("C") > order.index("A")
    assert order.index("C") > order.index("B")


def test_topological_order_raises_on_cycle() -> None:
    with pytest.raises(ValueError, match="invalid workflow graph"):
        topological_order(["A", "B"], [("A", "B"), ("B", "A")])


def test_topological_order_raises_on_duplicate_step() -> None:
    with pytest.raises(ValueError, match="invalid workflow graph"):
        topological_order(["A", "A"], [])


def test_topological_order_raises_on_self_dependency() -> None:
    with pytest.raises(ValueError, match="invalid workflow graph"):
        topological_order(["A"], [("A", "A")])


def test_topological_order_raises_on_empty_graph() -> None:
    with pytest.raises(ValueError, match="invalid workflow graph"):
        topological_order([], [])


def test_topological_order_raises_on_missing_endpoint() -> None:
    with pytest.raises(ValueError, match="invalid workflow graph"):
        topological_order(["B"], [("A", "B")])


def test_topological_order_raises_on_duplicate_edge() -> None:
    # Duplicate edges are rejected, not silently de-duplicated.
    with pytest.raises(ValueError, match="invalid workflow graph"):
        topological_order(["A", "B"], [("A", "B"), ("A", "B")])
