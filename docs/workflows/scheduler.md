# Workflow Scheduler (Phase 7.3)

Phase 7.3 adds **application-level scheduling** on top of the Phase 7.1
foundation and Phase 7.2 execution engine.

> **Phase 7.3 provides scheduling logic but does NOT introduce
> distributed/background worker infrastructure.** There is no Redis,
> Celery, Arq, daemon, queue, or distributed coordination anywhere here.
> Scheduling advances only when something calls it — an API request or a
> test. Nothing fires "by itself" in the background.
>
> *Phase 7.4 update:* the scheduler can now optionally ENQUEUE each run it
> creates (still never executing anything itself). See
> [queue-worker.md](queue-worker.md).

## Architecture

```
POST /workflows/schedules/evaluate        routes/schedules.py (thin)
  ↓
SchedulerService       services/scheduler.py   ← due detection, run creation
  ├── OccurrenceCalculator  workflows/scheduling.py  ← pure cron/timezone math
  ├── Clock                 workflows/scheduling.py  ← injectable time source
  └── repositories          persistence only
  ↓
creates pending WorkflowRun (+ StepRuns) via existing repository
  ↓
DAGExecutionEngine executes it (unchanged Phase 7.2 mechanism)
```

Responsibility boundaries are unchanged from earlier phases:

| Component | Owns | Never does |
| --- | --- | --- |
| `WorkflowService` | definition validation, manual run creation | scheduling, execution |
| `SchedulerService` | due detection, scheduled run creation, schedule lifecycle | executing steps |
| `OccurrenceCalculator` | occurrence math for a `ScheduleSpec` | I/O of any kind |
| `DAGExecutionEngine` | driving a pending run to a terminal state | scheduling |
| Repositories | persistence | deciding legality |

The scheduler creates runs through exactly the same repository path as
manual runs (`ordered_step_ids` → one pending `StepRun` per step in
topological order). It never transitions them.

## Schedule data model

`workflow_schedules` — one row per schedule, always bound to one workflow:

| Column | Purpose |
| --- | --- |
| `workflow_id` | FK → `workflows.id` (`ON DELETE CASCADE`) |
| `schedule_type` | `once` or `recurring` (CHECK-enforced) |
| `expression` | standard 5-field cron expression (recurring only) |
| `run_at` | absolute UTC instant (one-time only; CHECK keeps shape/type consistent) |
| `timezone_name` | IANA zone cron is evaluated in (default `UTC`) |
| `state` | `enabled` / `disabled` / `completed` (CHECK-enforced) |
| `next_run_at` | next occurrence to fire (UTC) |
| `last_run_at` | evaluation time when a run was last created |

The existing `workflow_runs` table gains two nullable columns:
`schedule_id` (FK, `ON DELETE SET NULL` — runs outlive their schedule)
and `scheduled_for` (the occurrence this run belongs to).

Cron parsing lives behind the `OccurrenceCalculator` abstraction
(`croniter` today); swapping expression languages would not touch the
service. Lifecycle transitions mirror the run-state pattern:
`SCHEDULE_STATE_TRANSITIONS`, `can_transition_schedule()`.

## Schedule lifecycle

```
enabled ⇄ disabled
   ↓ (one-time schedules only, after firing)
completed            (terminal)
```

- One-time schedules complete themselves after creating their single run.
- Recurring schedules stay enabled and receive a recomputed
  `next_run_at`.
- Disabled schedules are invisible to due detection — they can never
  create runs. Their `next_run_at` is frozen while disabled.
- Re-enabling recomputes `next_run_at` relative to *now*, so enabling
  never fires stale occurrences.
- Illegal moves (e.g. re-enabling a completed schedule) raise
  `ScheduleStateTransitionError` → HTTP 409.

## Due-run detection

`SchedulerService.evaluate_due(now=None)` performs one deterministic pass:

1. Load all **enabled** schedules (indexed by `(state, next_run_at)`).
2. A schedule is **due** iff `next_run_at is not None` and
   `next_run_at <= now` (exact boundary counts as due).
3. Create one pending `WorkflowRun` with
   `(schedule_id, scheduled_for=occurrence)` via
   `WorkflowRepository.create_scheduled_run`.
4. Advance bookkeeping in the same pass:
   - once → `last_run_at=now`, `next_run_at=None`, state `completed`;
   - recurring → `last_run_at=now`, `next_run_at` = first cron occurrence
     strictly after `now`, state stays `enabled`.

Lagging evaluations catch up exactly once per elapsed occurrence window:
the next occurrence is computed strictly after evaluation time, so a
late pass never double-fires the same wall-clock slot.

## Idempotency

Every scheduler-created run records `(schedule_id, scheduled_for)`, and a
**partial unique index**
`uq_workflow_runs_schedule_occurrence (schedule_id, scheduled_for)
WHERE schedule_id IS NOT NULL AND scheduled_for IS NOT NULL`
makes duplicate creation of one occurrence impossible at the database
level — even under concurrent evaluators. `create_scheduled_run`
translates a uniqueness violation into `None`; `evaluate_due` reports it
as `skipped_duplicates` instead of failing. Repeated evaluation of the
same time therefore creates exactly one run.

## Timezone handling

- All stored instants (`run_at`, `next_run_at`, `last_run_at`,
  `scheduled_for`) are timezone-aware UTC.
- Cron expressions are evaluated **in the schedule's own timezone** via
  `ZoneInfo`, then normalized to UTC — `0 9 * * *` with
  `Asia/Kathmandu` fires at 03:15 UTC every day.
- DST is handled by the calculator: wall-clock semantics follow the
  named zone across transitions (verified for America/New_York spring-
  forward).
- Naive timestamps are rejected everywhere: spec validation flags naive
  `run_at`, and `evaluate_due` refuses naive `now`. Core logic reads time
  only through the injected `Clock`.

## API

| Method & path | Purpose |
| --- | --- |
| `POST /workflows/{id}/schedules` | create (404 unknown workflow, 422 invalid config) |
| `GET /workflows/schedules?workflow_id=` | list, optional workflow filter |
| `GET /workflows/schedules/{sid}` | retrieve |
| `PATCH /workflows/schedules/{sid}` | update spec (recomputes `next_run_at` when enabled) |
| `POST /workflows/schedules/{sid}/enable` | enable (re-arms relative to now) |
| `POST /workflows/schedules/{sid}/disable` | disable |
| `DELETE /workflows/schedules/{sid}` | delete (204) |
| `POST /workflows/schedules/evaluate` | one synchronous due-detection pass |

`evaluate` is intentionally boring: it returns
`{evaluated_at, created_runs, skipped_duplicates}`. It does not pretend
to be a distributed scheduler. To run a workflow immediately without
waiting for its schedule, use the existing
`POST /workflows/{id}/runs` — no duplicate execution mechanism exists.

## Current application-level limitation

Evaluation happens **only when `/schedules/evaluate` is called** (or in
tests). There is no internal loop, timer, or worker that invokes it
periodically — that would require background infrastructure, which is
explicitly deferred. Operationally, an external trigger (cron, CI job,
human) may call the endpoint; each call is idempotent per occurrence, so
calling it too often or twice is safe.

## Deferred to later phases

- Background loop/timer invoking `evaluate_due` periodically
- Distributed schedulers, leader election, sharding
- Retry policies for missed windows, jitter, coalescing strategies
- Interval/range expression languages beyond standard cron
- Per-schedule execution hooks (auto-execute after creation)
