# Retry & Failure Handling

Phase 7.5 adds a controlled retry and failure-classification layer on top
of the Phase 7.4 queue/worker execution path. The worker never decides
on its own whether a failure is retryable — it delegates to an injected
`RetryPolicy`, which consults the failure class and the remaining
attempt budget.

---

## Failure Classification

Every execution failure is classified by `classify_failure` into one of
five deterministic classes:

| Class             | Typical causes                          | Auto-retryable? |
| ----------------- | --------------------------------------- | --------------- |
| `transient`       | Timeouts, connection resets, transient `TransientExecutionError` from executors | Yes (if policy allows) |
| `permanent`       | Bad input data, unsupported configuration, unmapped exceptions | Never by default |
| `cancellation`    | Run was cancelled mid-flight            | **Never** — hard rule |
| `invalid_workflow`| DAG has cycles, missing steps, `WorkflowValidationError` | Never by default |
| `infrastructure`  | Queue unavailable, job deserialization failure | Never auto-retried |

Classification precedence: the run state `cancelled` overrides the
exception type — a `TransientExecutionError` during a cancelled run
classifies as `cancellation`.

Unknown exception types default to `permanent` (conservative).

---

## Retry Policy

`RetryPolicy` is a frozen, serialisable dataclass:

```python
RetryPolicy(
    max_attempts=3,                  # total EXECUTION attempts allowed
    retryable=frozenset({FailureClass.TRANSIENT}),  # which classes retry
    backoff=ExponentialBackoff(      # delay strategy for the Nth retry
        initial=timedelta(seconds=1),
        multiplier=2.0,
        max_delay=timedelta(seconds=30),
    ),
)
```

- `max_attempts=1` disables automatic retries entirely (the Phase 7.4
  default).
- The `retryable` set is the ONLY knob that controls WHICH classes
  may be retried — no hidden rules.
- `decide(classification, attempts_made)` returns a `RetryDecision`
  with `retry: bool`, `reason: str`, and `delay: timedelta`.

Hard rules that no configuration can override:

1. Cancellation is never retried.
2. Infrastructure failures are never auto-retried (queue unavailable
   is not transient to the workflow — it is a deployment issue).

---

## Backoff Strategy

Deterministic — no jitter, no randomness, no wall-clock input.

| Strategy             | Formula                                      |
| -------------------- | -------------------------------------------- |
| `FixedBackoff(delay)`| Always returns `delay`                       |
| `ExponentialBackoff(initial, multiplier, max_delay)` | `initial × multiplier^(retry-1)`, clamped to `max_delay` |

`delay_for(retry_number)` — the retry index starts at 1 (first retry
after the first failure). Inputs beyond the cap return `max_delay`
without constructing large intermediate values.

---

## Attempt Tracking

New columns on `workflow_runs` (migration `a7c3d9e1b5f8`):

| Column          | Type       | Purpose                                        |
| --------------- | ---------- | ---------------------------------------------- |
| `attempt_count` | `INT`      | Number of execution attempts so far; incremented each time the engine starts a run |
| `failure_class` | `VARCHAR(32)` | Last failure classification                 |
| `next_retry_at` | `TIMESTAMPTZ` | When the next automatic retry should fire  |
| `failure_history`| `JSONB`   | Append-only list of `{attempt, class, reason, failed_at}` entries |

A retry never silently overwrites the previous attempt — history is
appended, not replaced.

---

## Retry Lifecycle

```
Worker receives job
  → claim from queue
  → classify as non-pending?
      YES → skip (idempotency guard)
  → FAILED + next_retry_at pending?
      → not due yet → reschedule in queue, skip execution
      → due → reopen run to PENDING, fall through to execute
  → execute via DAG engine
  → success → COMPLETE, release job
  → failure:
      1. Record failure metadata (classification + history)
      2. Park run in FAILED (except cancellation — keeps own state)
      3. Ask RetryPolicy.decide()
      4. retry=True:
           atomically reschedule replacement into the SAME queue
           persist next_retry_at for observability
      5. retry=False (exhausted / non-retryable):
           record final failure reason, release job
```

---

## Queue Integration

Retries re-enter through the **same** Phase 7.4 queue — no second queue,
no bypass.

Key operation: `JobQueue.reschedule(job, delay)` — atomically releases
the current claimed job and pushes a replacement with a `delay` into
the scheduled set. The two-step is indivisible so a worker crash
between them cannot silently stall a retry.

Delayed jobs live in a ZSET (`:scheduled`, Redis) or a heapq (in-memory)
and are promoted to the claimable list when their ready time arrives.

---

## Idempotency Protections

| Scenario                    | Protection                                           |
| --------------------------- | ---------------------------------------------------- |
| Duplicate delivery          | Pre-flight state guard: non-pending runs are skipped |
| Duplicate retry scheduling  | `reschedule` replaces the active claim; `_by_run` deduplicates |
| Worker crash                | Claimed job stays on processing list for later recovery |
| Retry of already-completed  | `reopen_run_for_retry` only accepts FAILED → returns None otherwise |
| Retry after cancellation    | Classification = `cancellation` → policy says no retry |
| Retry beyond max attempts   | `attempts_made >= max_attempts` → budget exhausted, final failure |
| Concurrent execution        | `_active_by_run` guard blocks a second enqueue for the same run |

---

## Final Failure / Dead-Letter

When the retry budget is exhausted, or the failure class is not
retryable, the run stays FAILED with its full `failure_history` intact.
The FAILED run itself **is** the dead-letter record — no physical
dead-letter queue is introduced, and nothing keeps requeueing the job.

---

## Manual Retry

`POST /workflows/runs/{run_id}/retry` allows an operator to re-execute a FAILED
run regardless of the retry budget:

- Only FAILED runs qualify — anything else returns 409.
- The automatic retry policy is NOT consulted.
- The run is reopened to PENDING and enqueued immediately through the
  same queue/worker path.

---

## Limitations

- No per-step retry (workflow-level only in this phase)
- No jitter — all backoff is deterministic
- No distributed multi-region retry coordination
- No dead-letter platform — final failure is a database record only
