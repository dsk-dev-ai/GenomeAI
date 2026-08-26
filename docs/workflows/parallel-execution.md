# Parallel DAG Execution

Phase 7.6 extends the Phase 7.2 DAG execution engine with concurrent
execution of independent workflow steps. When `max_concurrency` > 1,
steps that have all their dependencies satisfied run simultaneously
using Python's structured concurrency (`asyncio.TaskGroup`).

---

## Configuration

```python
DAGExecutionEngine(
    repository=store,
    executor=executor,
    max_concurrency=4,  # up to 4 steps run concurrently
)
```

| `max_concurrency` | Behaviour |
| ----------------- | --------- |
| `1` (default)     | Sequential — identical to Phase 7.2 |
| `N > 1`           | Up to N independent steps execute concurrently |

`max_concurrency < 1` raises `ValueError` at construction time.

---

## Execution Model

The engine processes the DAG in **waves**:

1. Rebuild the `PlannedStep` list from current in-memory states.
2. Call `ready_steps()` — returns all PENDING steps whose ALL direct
   predecessors have SUCCEEDED.
3. If no steps are ready and none are running, the run is complete.
4. Launch all ready steps as concurrent tasks via `asyncio.TaskGroup`,
   gated by an `asyncio.Semaphore(max_concurrency)`.
5. Each task transitions its step to RUNNING, invokes the executor
   (via `asyncio.to_thread` for synchronous executors), and records
   the outcome.
6. After all tasks in the wave complete, re-enter step 1.

**Example — diamond DAG:**

```
    a
   / \
  b   c     ← wave 2: b and c run concurrently
   \ /
    d       ← wave 3: d waits for both b and c
```

---

## Concurrency Enforcement

An `asyncio.Semaphore(max_concurrency)` gates task startup. Tasks
beyond the limit queue on the semaphore and execute as earlier tasks
complete. The watermark (peak concurrent count) is a testable property
of the executor.

---

## Structured Concurrency

All concurrent tasks are children of a single `asyncio.TaskGroup`. The
engine waits for every task to complete (success, failure, or early
return) before re-evaluating the DAG. No task outlives the engine
method — there are no detached fire-and-forget tasks.

---

## Failure Handling in Parallel Mode

When a concurrent step fails:

1. The failure is recorded on the step (FAILED + error message).
2. A shared `asyncio.Event` (`cancel_event`) is set, preventing any
   NEW step from starting.
3. Steps that are already running complete their current executor call
   and record their actual outcome (success or failure).
4. After the wave completes, the engine sweeps all PENDING steps to
   CANCELLED and transitions the run to FAILED.

**Race condition safety:** Multiple concurrent steps may fail in the
same wave. The first failure recorded wins the `failure_step_name` and
`failure_reason` — the second sees `cancel_event` already set and
silently returns. All failures are still persisted on their respective
step runs.

---

## Cancellation in Parallel Mode

Cancellation (`should_cancel()` callback) is checked at two points:

1. **Before wave start:** the `while True` loop checks
   `_should_cancel()` before computing ready steps.
2. **Inside each task:** before acquiring the semaphore and before
   the executor call, each task checks `_should_cancel()`.

If cancellation is detected, completed steps retain their SUCCEEDED
state; pending steps are swept to CANCELLED; the run transitions to
CANCELLED. Unlike failure mode, no step is marked FAILED.

---

## Sync Executor Integration

`StepExecutor.execute()` is synchronous. The engine wraps each call
with `asyncio.to_thread()`, which offloads the blocking call to the
default thread pool. The repository/state mutations remain in the
event loop (single-threaded, safe for in-memory fakes in tests).

---

## Data Flow

Upstream outputs are assembled from the in-memory `outputs` dict
populated by earlier waves. Because waves complete before the next
wave starts, all upstream data is available when the downstream step
begins. The `StepExecutionContext.upstream_outputs` mapping is
identical to the sequential model.

---

## Backward Compatibility

- `max_concurrency=1` (default) produces identical behaviour to
  Phase 7.2. All 13 original engine tests pass without modification.
- The `ExecutionRunStore` protocol is unchanged.
- The `StepExecutor` protocol is unchanged.
- No database migration is required — parallelism is an execution-time
  concern only.
- Worker and API entry points pass `max_concurrency` through the
  engine constructor; existing callers default to 1.

---

## Testing

18 parallel-specific tests in `tests/test_workflow_parallel_execution.py`:

| Category | Tests |
| -------- | ----- |
| Concurrency verification | watermark, limit enforcement, sequential match |
| DAG shapes | diamond, wide fan-out, complex mixed |
| Failure handling | dependent cancellation, independent preservation, wave blocking, exception, dual failure |
| Cancellation | before start, during execution, stops new steps |
| Regression | linear order, output flow, invalid config, single step |

---

## Limitations

- No per-step concurrency override (global limit only)
- No dynamic concurrency adjustment during execution
- No priority-based step scheduling
- No cross-run parallelism (one run at a time per engine instance)
- Sync executors run in threads via `asyncio.to_thread` — not
  suitable for CPU-bound work without GIL consideration
