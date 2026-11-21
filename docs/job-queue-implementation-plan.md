# Job Queue Implementation Plan

**Repository:**
[Mdwiki-TD/svg_translate_web](https://github.com/Mdwiki-TD/svg_translate_web)\
**Proposed branch:** `feature/job-queue`\
**Target branch:** `main`\
**Status:** Proposal only --- no repository changes have been made.

## 1. Objective

Introduce a persistent FIFO job queue so that users can submit a job
even when another job of the same type is already running.

The current application rejects such requests with:

> A job of this type is already running. Please wait for it to complete.

Instead, new jobs should be accepted, stored, and queued. The next
eligible job should start automatically when the currently running job
of the same type reaches a terminal state.

### Scope and constraints

- Do not modify `main`.
- Do not deploy changes to production as part of this work.
- Implement the feature on a dedicated branch created from the latest
  `main`.
- Submit the work through a Pull Request for review.
- Preserve the existing job execution backend and cancellation
  behavior wherever possible.
- Avoid introducing Redis, Celery, or another external queueing
  dependency in the initial implementation.

## 2. Current Architecture and Problem

The relevant existing components include:

---

Component Current responsibility

---

`database/models/jobs.py` SQLAlchemy job model and database
constraints

`database/services/jobs_service.py` Job persistence and status
management

`jobs_workers/jobs_lifetime/jobs_starter.py` Job creation and execution startup

`jobs_workers/backends/` Background execution backends

`public/shared_jobs_routes.py` Shared request handling for
starting and managing jobs

---

The `jobs` table currently has a unique constraint:

```python
UniqueConstraint("job_type", "is_running", name="idx_unique_active_job")
```

The intended behavior of this constraint is to allow only one active job
per `job_type`. A running job uses `is_running = 1`; inactive rows use
`NULL`. MySQL permits multiple `NULL` values in a unique index, so
completed and otherwise inactive jobs do not conflict.

The current job creation path reserves the active-job slot when the job
record is created. As a result, a second request for the same `job_type`
raises `DuplicateRecordError` before it can be accepted for later
execution.

The queue implementation must distinguish between **waiting** and
**running** jobs. A waiting job must not reserve the unique active-job
slot.

## 3. Proposed Design

Implement a database-backed FIFO queue using the existing `jobs` table
and SQLAlchemy services.

The database remains the durable source of truth. A dispatcher selects
the oldest eligible pending job and atomically claims it before handing
it to the existing backend.

### High-level lifecycle

1.  A user submits a job.
2.  The application validates the request and permissions.
3.  A job record is created with `status = "pending"` and
    `is_running = NULL`.
4.  The job's execution payload is persisted safely.
5.  The dispatcher checks whether a job of this type is already running.
6.  If no job of this type is running, the dispatcher atomically claims
    the oldest pending job and starts it.
7.  If another job of the same type is running, the new job remains
    queued.
8.  When the running job completes, fails, or is cancelled, the
    dispatcher attempts to start the next pending job of that type.

Different job types may continue to execute concurrently, subject to the
application's existing resource and backend limits.

## 4. Job States and Database Semantics

Reuse the existing `jobs` table. A separate queue table should not be
necessary for the initial implementation.

---

State `status` `is_running` Meaning

---

Waiting `pending` `NULL` Accepted and
waiting for its
turn

Running `running` `1` Holds the active
slot for its job
type

Completed `completed` `NULL` Finished
successfully

Failed `failed` `NULL` Execution failed

Cancelled `cancelled` `NULL` Cancelled before
or during
execution

---

The existing unique constraint can remain in place:

```python
UniqueConstraint("job_type", "is_running", name="idx_unique_active_job")
```

This preserves the database-level invariant that only one job of a given
type can hold the active slot.

### Important implementation detail

The transition from `pending` to `running` must be atomic. The
dispatcher must claim a job only if no other job of the same type
currently holds the active slot.

Do not set `is_running = 1` when merely enqueueing a job. Doing so would
prevent multiple jobs of the same type from entering the queue.

The implementation must use database transactions and a concurrency-safe
claim strategy. It must handle unique-constraint conflicts and
concurrent dispatch attempts without starting duplicate executions.

## 5. Queue Service

Add a dedicated service, for example:

`jobs_workers/jobs_lifetime/jobs_queue.py`

The service should own queue selection, claiming, dispatching, and
pending-job cancellation. Keep route handlers and `JobStarter` free from
queue-ordering and locking details.

Suggested operations:

---

Method Responsibility

---

`enqueue()` Persist a new pending job and its
execution payload

`get_next_pending()` Select the oldest eligible pending
job for a job type

`claim_job()` Atomically reserve the active slot
and transition the job to running

`dispatch_next()` Claim and submit the next eligible
job to the backend

`dispatch_pending()` Scan for pending work and attempt
dispatch

`cancel_pending()` Cancel a job that has not started

---

### FIFO ordering

Use a deterministic ordering:

```sql
ORDER BY created_at ASC, id ASC
```

The `id` is the tie-breaker when multiple jobs have the same creation
timestamp.

The queue should be FIFO within each `job_type`. Jobs of different types
do not need to share one global execution order.

### Concurrency and atomic claiming

The queue must remain correct when multiple web workers or dispatcher
processes run simultaneously.

The implementation should:

- Use a short database transaction for selecting and claiming a job.
- Ensure only one process can claim a given active slot.
- Rely on the database unique constraint as a final integrity guard.
- Handle an `IntegrityError` or the project's equivalent
  duplicate-record exception as a normal claim race where appropriate.
- Avoid holding database locks while the actual job executes.
- Ensure a failed backend submission releases the active slot and
  records a failure state.

Choose the simplest transaction and locking approach supported by the
project's current database engine and SQLAlchemy version. Document any
database-specific behavior relied upon.

## 6. JobStarter Integration

Change the job startup flow from direct execution:

```text
JobStarter -> Backend
```

to queue-based submission:

```text
JobStarter -> JobsQueue -> Backend
```

`JobStarter` should continue to validate the job type, resolve
configured arguments, sanitize sensitive or unnecessary fields, and
preserve the existing public method signatures where practical.

Its responsibility should become:

1.  Validate the requested job type and user.
2.  Resolve and sanitize job arguments.
3.  Create a pending job record.
4.  Persist the job payload.
5.  Ask the queue dispatcher to process eligible work.
6.  Return the created job ID, whether it starts immediately or waits.

The caller should no longer receive `DuplicateRecordError` merely
because another job of the same type is running.

### Backend compatibility

Keep the current backend abstraction and `ThreadBackend` behavior. The
queue decides **when** a job is eligible to start; the backend remains
responsible for **how** the job executes.

Do not bypass existing backend interfaces or duplicate execution logic
inside the queue service.

## 7. Durable Job Payloads and User Identity

A queued job may wait for minutes or longer. Its execution data must
therefore survive web process restarts.

Do not rely on in-memory Python objects, request context, Flask `g`, or
a live HTTP request to retain the job's payload.

Persist the data required to reconstruct execution, including:

- Job arguments (`args`).
- Form data (`form_data`), after removing CSRF tokens and other
  non-persistent or sensitive fields.
- The username associated with the job record.

Do not store OAuth access tokens or secrets as plaintext in the queue
payload.

When a queued job is dispatched, rebuild the execution identity using
the application's existing user-token and authentication services, based
on the persisted job username. Follow the project's established
encryption and token-handling patterns.

If the user's credentials are unavailable when the job is eventually
started, fail the job with a clear, non-sensitive error message and
release the active slot.

## 8. Dispatch Triggers and Recovery

The dispatcher should be invoked at the following points:

1.  **After enqueueing:** Start the job immediately if its type has no
    active job.
2.  **After successful completion:** Dispatch the next pending job of
    the same type.
3.  **After failure:** Release the active slot and dispatch the next
    pending job.
4.  **After cancellation:** Once the previous execution has actually
    stopped and the active slot is safely released, dispatch the next
    pending job.
5.  **After application startup:** Recover and dispatch eligible pending
    jobs.
6.  **Periodic recovery:** Run a periodic dispatcher/reconciliation
    process to recover from missed triggers or process restarts.

### Recovery requirements

A periodic recovery mechanism is important because a process may
terminate after a job is persisted but before dispatch is triggered.

Recovery must distinguish between:

- A legitimate pending job.
- A running job whose worker is still alive.
- A stale running record whose execution has disappeared.
- A job whose backend submission failed.
- A terminal job that no longer holds an active slot.

Do not automatically mark a running job as failed merely because a web
process restarted. The job may be executing in another process. Recovery
must use the project's actual backend and execution-state information
where available.

The initial implementation should reuse existing job lifecycle and
reconciliation facilities rather than introducing an unnecessarily
complex scheduler.

## 9. Cancellation Behavior

Cancellation must work differently depending on whether the job has
started.

### Pending job

- Verify that the requesting user is authorized to cancel it.
- Transition it directly to `cancelled`.
- Do not invoke the execution backend.
- Ensure it never becomes eligible for dispatch.
- Update the queue position of remaining pending jobs in the UI.

### Running job

- Preserve the existing cancellation mechanism.
- Do not release the active slot until the previous execution has
  actually stopped, or until the existing cancellation lifecycle can
  safely guarantee that it has stopped.
- Dispatch the next job only after the active slot is safely
  available.

**Critical race condition:** Releasing the unique active slot
immediately when cancellation is requested may allow a second job of the
same type to start while the first one is still executing. The
implementation must prevent this overlap.

## 10. User Interface

Update the job list and job detail views to make queue state visible.

Suggested status labels:

- `Running`
- `Queued · #1`
- `Queued · #2`
- `Queued · #3`
- `Completed`
- `Failed`
- `Cancelled`

For pending jobs, display their current position within the queue for
their `job_type`.

When a user submits a job, show a message such as:

> Your job has been added to the queue. Its current position is 3.

The position should be calculated from the current pending jobs of the
same type, ordered by `created_at` and `id`. It is informational and may
change as jobs are completed or cancelled.

Where the existing UI supports it, allow users to cancel their own
pending jobs. Administrators should retain the existing administrative
permissions.

Do not expose another user's sensitive job arguments, form data,
credentials, or private execution details when displaying queue
information.

## 11. Error Handling

The queue must handle failures at each stage.

---

Failure Expected behavior

---

Job record creation fails Return an error; do not create a
phantom queue entry

Payload persistence fails Mark or roll back the job safely;
do not dispatch without a complete
payload

Another dispatcher claims the slot Treat as a normal concurrency race;
leave the job pending

Backend submission fails Mark the claimed job failed and
release its active slot

Job execution fails Preserve the failure details,
release the slot, and dispatch the
next job

User credentials are unavailable Fail safely without logging secrets

Dispatcher is interrupted Recover pending work through
startup or periodic dispatch

Cancellation is requested Do not start the next job until the
previous execution has stopped

---

A failure in one job must not permanently block the remaining queue.

## 12. Testing Plan

Add focused unit and integration tests using the repository's existing
testing conventions.

### Queue behavior

1.  Submit three jobs of the same type; verify that all three are
    accepted.
2.  Verify that only the first job starts.
3.  Complete the first job and verify that the second starts.
4.  Complete the second job and verify that the third starts.
5.  Verify FIFO ordering using `created_at` and `id`.
6.  Verify that different job types can run concurrently.

### Failure handling

7.  Fail a running job and verify that the next pending job starts.
8.  Simulate backend submission failure and verify that the active slot
    is released.
9.  Simulate payload persistence failure and verify that no incomplete
    job is dispatched.
10. Verify that unavailable user credentials result in a safe failure.

### Cancellation

11. Cancel a pending job and verify that its backend is never invoked.
12. Cancel a running job and verify that the next job does not start
    prematurely.
13. Verify that a cancelled pending job is skipped by the dispatcher.

### Concurrency and recovery

14. Simulate two dispatchers attempting to claim the same job type.
15. Verify that the database constraint prevents duplicate active
    claims.
16. Simulate application restart with pending jobs and verify recovery.
17. Verify that a stale or failed dispatch does not block the queue.
18. Verify that repeated dispatcher calls are safe and idempotent.

### UI and permissions

19. Verify that the submission response distinguishes immediate
    execution from queueing.
20. Verify that queue positions are calculated per job type.
21. Verify that users can cancel only jobs they are authorized to
    manage.
22. Verify that administrators retain their existing management
    capabilities.

Tests should assert observable behavior and expected database states.
Use real test functions and expected outputs, following the project's
current test structure.

## 13. Implementation Phases

### Phase 1 --- Inspect and document current lifecycle

- Trace job creation, status transitions, backend startup, completion,
  failure, and cancellation.
- Identify every place where the active slot is acquired or released.
- Confirm how job payloads are currently persisted and reconstructed.
- Confirm the database engine and transaction behavior.
- Identify existing startup hooks and periodic jobs that can support
  recovery.

**Deliverable:** A verified lifecycle map and a list of integration
points.

### Phase 2 --- Implement the queue service

- Add `jobs_queue.py`.
- Implement FIFO selection.
- Implement atomic active-slot claiming.
- Implement pending-job cancellation.
- Add safe handling for concurrent dispatch attempts.
- Keep the existing unique constraint as the final active-slot guard.

**Deliverable:** Queue service with unit tests.

### Phase 3 --- Integrate job creation and execution

- Change `JobStarter` to enqueue instead of directly rejecting
  duplicate job types.
- Persist the execution payload durably.
- Dispatch immediately when the type is available.
- Preserve backend compatibility and public startup interfaces.
- Handle backend startup failures without leaving a stuck active slot.

**Deliverable:** End-to-end queue execution using the existing backend.

### Phase 4 --- Integrate completion, failure, and cancellation

- Trigger the next dispatch after terminal state transitions.
- Ensure the active slot is released consistently.
- Prevent overlap during cancellation.
- Add startup and periodic recovery.

**Deliverable:** Reliable queue progression and recovery.

### Phase 5 --- Update the UI

- Display queued status and queue position.
- Show a suitable submission confirmation.
- Support cancellation of pending jobs.
- Preserve existing permissions and job detail behavior.

**Deliverable:** User-visible queue state.

### Phase 6 --- Verification and Pull Request

- Run focused unit tests.
- Run relevant existing regression tests.
- Run integration tests for sequential execution and concurrency.
- Review transaction boundaries and cancellation races.
- Verify that no production deployment is triggered.
- Open a Pull Request from `feature/job-queue` to `main`.

**Deliverable:** Reviewed Pull Request with test results and
implementation notes.

## 14. Acceptance Criteria

The feature is ready for review when all of the following are true:

- Users can submit multiple jobs of the same type.
- Jobs are persisted and remain queued across web process restarts.
- Only one job per `job_type` holds the active slot at a time.
- Pending jobs execute in FIFO order within their job type.
- Different job types can execute concurrently.
- Completion, failure, and cancellation advance the queue correctly.
- A pending job can be cancelled without invoking a backend.
- A running job's active slot is not released prematurely during
  cancellation.
- Concurrent dispatchers cannot start duplicate jobs of the same type.
- Backend startup failures do not leave permanently locked job types.
- Queue status and position are visible in the UI.
- Existing job permissions and authentication rules remain enforced.
- Existing backend behavior and unrelated job types are not regressed.
- Automated tests cover queue ordering, concurrency, recovery, and
  cancellation.
- All changes are contained in the dedicated feature branch and
  delivered through a Pull Request.

## 15. Branching and Production Safety

All implementation work must follow this workflow:

```text
main
 |
 +-- feature/job-queue
       |
       +-- Queue service
       +-- Database/service integration
       +-- JobStarter integration
       +-- Lifecycle and recovery integration
       +-- UI updates
       +-- Tests
       |
       +-- Pull Request -> main
```

Rules:

1.  Start from the latest `main`.
2.  Create and work only on `feature/job-queue` (or another explicitly
    agreed feature branch).
3.  Do not commit directly to `main`.
4.  Do not merge the Pull Request without review and approval.
5.  Do not trigger production deployment during implementation or
    testing.
6.  Check repository CI and deployment workflows before pushing changes,
    because repository automation may deploy changes after certain
    branch or merge events.
7.  Clearly document any required database migration and deployment
    order in the Pull Request.
8.  Do not apply schema changes to production as part of this proposal.

## 16. Out of Scope for the Initial Version

To keep the implementation focused, the first version should not
include:

- Redis or Celery integration.
- Distributed priority scheduling.
- User-configurable queue priorities.
- A global concurrency limit across all job types.
- Automatic retries of failed jobs.
- A separate queue-management dashboard for administrators beyond the
  existing job UI.
- Changes to unrelated job execution logic.

These can be considered later if actual workload or operational
requirements justify them.

## 17. Final Architectural Recommendation

Use the existing SQL database as the durable queue, the existing `jobs`
table as the job record, and the current backend abstraction as the
execution mechanism.

The key architectural separation is:

- **JobStarter:** validates and submits jobs.
- **JobsQueue:** orders, claims, and dispatches jobs.
- **Backend:** executes a claimed job.
- **JobsService:** persists and updates job state.
- **Lifecycle hooks and recovery:** advance the queue and recover
  missed dispatches.

This approach addresses the current duplicate-job rejection with
relatively limited architectural change. It preserves the existing
one-active-job-per-type invariant while allowing any number of pending
jobs, and avoids adding external infrastructure before it is needed.

---

**Document status:** Implementation plan only. No code, branch, database
schema, or production environment has been modified.
