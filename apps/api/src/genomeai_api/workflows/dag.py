"""Deterministic DAG validation for workflow definitions.

Pure functions only — no I/O, no ORM. The same input always produces the same
issues in the same order, so validation is fully reproducible and trivially
testable.

A workflow graph is a set of step names plus directed edges ``from → to``
(meaning "to" may start once "from" has finished). Cycles, self-loops,
missing endpoints, duplicates, and empty graphs are all rejected here before
anything reaches the database.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class GraphIssue:
    """One deterministic validation problem, safe to surface to API clients."""

    code: str
    message: str


def validate_graph(
    step_names: list[str],
    edges: list[tuple[str, str]],
) -> list[GraphIssue]:
    """Validates a raw workflow graph and returns every issue found.

    Issue order is deterministic (structural checks first, then cycle check),
    and messages are stable, so identical inputs yield identical outputs.
    """
    issues: list[GraphIssue] = []

    if not step_names:
        issues.append(GraphIssue("empty-workflow", "Workflow must contain at least one step"))

    seen: set[str] = set()
    duplicates: set[str] = set()
    for name in step_names:
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    for name in sorted(duplicates):
        issues.append(
            GraphIssue("duplicate-step", f"Step name '{name}' is used more than once")
        )

    unique_edges: list[tuple[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()
    for source, target in edges:
        if source == target:
            issues.append(
                GraphIssue("self-dependency", f"Step '{source}' cannot depend on itself")
            )
            continue
        if source not in seen:
            issues.append(
                GraphIssue(
                    "missing-step",
                    f"Dependency references unknown step '{source}'",
                )
            )
            continue
        if target not in seen:
            issues.append(
                GraphIssue(
                    "missing-step",
                    f"Dependency references unknown step '{target}'",
                )
            )
            continue
        if (source, target) in seen_edges:
            issues.append(
                GraphIssue(
                    "duplicate-dependency",
                    f"Dependency '{source}' -> '{target}' is declared more than once",
                )
            )
            continue
        seen_edges.add((source, target))
        unique_edges.append((source, target))

    issues.extend(_cycle_issues(seen, unique_edges))
    return issues


def _cycle_issues(nodes: set[str], edges: list[tuple[str, str]]) -> list[GraphIssue]:
    """Kahn's algorithm; anything unprocessed participates in a cycle."""
    indegree: dict[str, int] = {name: 0 for name in nodes}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        adjacency[source].append(target)
        indegree[target] += 1

    ready = sorted(name for name, degree in indegree.items() if degree == 0)
    processed = 0
    while ready:
        current = ready.pop(0)
        processed += 1
        for neighbour in adjacency[current]:
            indegree[neighbour] -= 1
            if indegree[neighbour] == 0:
                ready.append(neighbour)
                ready.sort()

    if processed == len(nodes):
        return []

    cyclic = sorted(name for name, degree in indegree.items() if degree > 0)
    return [
        GraphIssue(
            "cycle",
            "Dependency cycle detected involving steps: " + ", ".join(cyclic),
        )
    ]


def topological_order(step_names: list[str], edges: list[tuple[str, str]]) -> list[str]:
    """Deterministic topological order (Kahn's algorithm, lexicographic tie-break).

    Raises :class:`ValueError` when the graph is invalid for ANY reason —
    cycles, empty inputs, duplicate steps, self-dependencies, missing
    endpoints, or duplicate edges (the same contract as
    :func:`validate_graph`). Duplicate edges are rejected, not silently
    de-duplicated, so callers see the same definition of "valid" everywhere.
    """
    issues = validate_graph(step_names, edges)
    if issues:
        raise ValueError(
            f"Cannot order an invalid workflow graph ({len(issues)} issue(s))"
        )

    indegree: dict[str, int] = {name: 0 for name in step_names}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        adjacency[source].append(target)
        indegree[target] += 1

    ready = sorted(name for name, degree in indegree.items() if degree == 0)
    ordered: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for neighbour in adjacency[current]:
            indegree[neighbour] -= 1
            if indegree[neighbour] == 0:
                ready.append(neighbour)
                ready.sort()
    return ordered


__all__ = ["GraphIssue", "topological_order", "validate_graph"]
