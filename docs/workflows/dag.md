# DAG Validation

Workflow graphs are validated by pure, deterministic functions in
`apps/api/src/genomeai_api/workflows/dag.py`. No I/O, no ORM — the same
input always yields the same issues in the same order.

## Graph model

- A workflow is a set of **step names** plus directed edges `from → to`
  ("`to` may start once `from` has finished").
- In the API, dependencies reference steps **by name** (the client cannot
  know database ids before creation). The service resolves names to ids
  after validation.
- In the database the graph is normalized: one row per step, one row per
  edge (`workflow_dependencies`). The DAG is never stored as JSON.

## Validation rules

`validate_graph(step_names, edges) -> list[GraphIssue]`

| Code | Trigger |
| --- | --- |
| `empty-workflow` | zero steps |
| `duplicate-step` | a step name used more than once |
| `self-dependency` | an edge whose source equals its target (checked before missing-step) |
| `missing-step` | an edge referencing a step that does not exist |
| `duplicate-dependency` | the same edge declared twice |
| `cycle` | Kahn's algorithm finds nodes that can never reach indegree 0 |

Issue order is deterministic: structural checks first (in input order,
duplicates sorted), then at most one aggregated `cycle` issue listing every
involved step. Identical inputs produce byte-identical issue lists, which
makes API error responses reproducible and testable.

## Topological ordering

`topological_order(step_names, edges)` implements Kahn's algorithm with a
**lexicographic tie-break**: whenever several steps are simultaneously
ready, the alphabetically smallest name is emitted first. For a branching
graph this makes run initialization fully deterministic regardless of how
steps were stored:

```
A → B        topological_order ⇒ [A, B, C]
A → C
```

The function raises `ValueError` for **any** invalid graph — cycles, empty
inputs, duplicate steps, self-dependencies, missing endpoints, or duplicate
edges — the exact same contract as `validate_graph` (duplicates are
rejected, not silently de-duplicated). Callers can therefore rely on one
definition of "valid" everywhere. The service does so on every path that
reaches it.

## Examples

Valid linear:

```
A → B → C        no issues
```

Valid branching / joining:

```
A → B            A → C
A → C            B → C
```

Invalid:

```
A → B            A → A
B → A            (self-dependency)
(cycle)
```

Invalid references:

```
steps: [B]       edge A → Z      both endpoints unknown → missing-step
edge X → B       source unknown  → missing-step
```

## Where validation runs

1. **Definition creation** — `WorkflowService.create_workflow` validates the
   submitted payload *before* any persistence; failures raise
   `WorkflowValidationError`, surfaced by the API as HTTP 422 with the full
   `issues` list.
2. **Run creation** — stored definitions were validated at creation time;
   the service re-derives the topological order from persisted edges when a
   run is requested.
