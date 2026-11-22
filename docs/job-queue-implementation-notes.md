# Job Queue — Implementation Notes

**Branch:** `feature/job-queue`
**Plan:** [`docs/job-queue-implementation-plan.md`](job-queue-implementation-plan.md)
**Status:** Implemented, covered by tests. No schema migration required.

---

## 1. Summary

Jobs are now accepted into a persistent FIFO queue instead of being rejected
when another job of the same type is running.

```text
JobStarter  ->  JobsQueue  ->  JobBackend (ThreadBackend)
                    |
                JobsService (jobs table = durable source of truth)
```

- **Waiting:** `status = 'pending'`, `is_running = NULL` — no active slot held.
- **Running:** `status = 'running'`, `is_running = 1` — holds the unique slot.
- **Terminal:** `completed` / `failed` / `cancelled` / `skipped`, `is_running = NULL`.

The existing unique constraint is unchanged and remains the final guard:

```python
UniqueConstraint("job_type", "is_running", name="idx_unique_active_job")
```

**No database migration is needed** — the queue reuses the existing `jobs`
table and columns. MySQL and SQLite both treat `NULL` as distinct in a unique
index, so any number of pending rows can coexist while only one row per
`job_type` can hold `is_running = 1`.

## 2. Verified lifecycle map (Phase 1 deliverable)

| Step                             | Code location                                                                                                                                  | Slot                        |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| Submit                           | `public/shared_jobs_routes.py::SharedJobRoutes.start_job_handler` → `jobs_lifetime/jobs_starter.py::JobStarter.submit_form`                    | —                           |
| Enqueue (persist job + payload)  | `jobs_lifetime/jobs_queue.py::JobsQueue.enqueue` → `JobsService.enqueue_job` + `JobFilesService.save_payload`                                  | not taken                   |
| Claim (atomic pending → running) | `JobsService.claim_pending_job` (single conditional `UPDATE`, `IntegrityError` = lost race)                                                    | **taken**                   |
| Execute                          | `backends/thread_backend.py::ThreadBackend.start` → `_runner` → `BaseObjectsJobWorker.run`                                                     | held                        |
| Complete / fail                  | `base_worker.py::after_run` → `JobsService._update_job_status` (final statuses set `is_running = NULL`)                                        | released                    |
| Cancel (queued)                  | `jobs_lifetime/jobs_canceller.py::JobCanceller.cancel` → `JobsQueue.cancel_pending` → `JobsService.cancel_pending_job` (backend never invoked) | never taken                 |
| Cancel (running)                 | `JobCanceller.cancel` → cancel event + `.cancelled` marker + `JobsService.cancel_job_db` (status becomes `cancelled`, **slot kept**)           | held until the worker stops |
| Advance the queue                | `thread_backend._runner` `finally` → `JobsQueue.on_job_finished` → `dispatch_next`                                                             | next job claims             |
| Startup recovery                 | `database/__init__.py::init_db` → `cleanup_stale_jobs_on_startup` + `JobsQueue.recover(force=True)`                                            | released / reclaimed        |
| Periodic recovery                | `flask dispatch-jobs` CLI (`toolforge/shs/dispatch_jobs.sh`) → `JobsQueue.recover(force=True)`                                                 | released / reclaimed        |

## 3. New and changed files

### New

| File                                                               | Purpose                                                                 |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| `www/python/src/main_app/jobs_workers/jobs_lifetime/jobs_queue.py` | `JobsQueue`, `JobIdentityResolver`, `EnqueueResult`, `sanitize_payload` |
| `toolforge/shs/dispatch_jobs.sh`                                   | Cron-friendly periodic recovery (`flask dispatch-jobs`)                 |
| `tests/unit/jobs_workers/jobs_lifetime/test_jobs_queue.py`         | Queue behaviour, FIFO, claims, failures, cancellation, recovery         |
| `tests/unit/jobs_workers/jobs_lifetime/test_queue_lifecycle.py`    | Cancellation races, backend finish hook, startup recovery               |
| `tests/integration/admin/routes/test_jobs_queue_ui.py`             | Queue position rendering + submission feedback                          |

### Changed

| File                                                                                                                               | Change                                                                                                                                                                                                                                                                                                 |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `database/services/jobs_service.py`                                                                                                | Queue primitives: `enqueue_job`, `claim_pending_job`, `has_running_job`, `list_pending_jobs`, `list_pending_job_types`, `get_queue_position(s)`, `cancel_pending_job`, `release_active_slot`, `fail_job`, `release_stale_active_slots`; `cancel_job_db` no longer releases the slot of a _running_ job |
| `io/jobs_files_service.py`                                                                                                         | Durable payload store: `payload_file_name`, `save_payload`, `load_payload`, `delete_payload`                                                                                                                                                                                                           |
| `services/auth/token_manager.py`                                                                                                   | `get_auth_payload_by_username()` — rebuilds execution identity from the persisted username                                                                                                                                                                                                             |
| `jobs_workers/jobs_lifetime/jobs_starter.py`                                                                                       | Submits through the queue (`submit`/`submit_form`), keeps `start`/`start_form`/`start_cli` returning the job id                                                                                                                                                                                        |
| `jobs_workers/jobs_lifetime/jobs_canceller.py`                                                                                     | Cancels queued jobs without touching a backend; keeps running-job semantics                                                                                                                                                                                                                            |
| `jobs_workers/backends/thread_backend.py`                                                                                          | Advances the queue when a job's execution really stopped                                                                                                                                                                                                                                               |
| `jobs_workers/objects.py`                                                                                                          | `JobsRunner.job_type` (needed to advance the right queue)                                                                                                                                                                                                                                              |
| `jobs_workers/cli_jobs.py`                                                                                                         | `flask dispatch-jobs` recovery command                                                                                                                                                                                                                                                                 |
| `database/__init__.py`                                                                                                             | Startup queue recovery (gated by `JOBS_QUEUE_STARTUP_DISPATCH`)                                                                                                                                                                                                                                        |
| `config/flask_config.py`                                                                                                           | `JOBS_QUEUE_STARTUP_DISPATCH` (disabled for `TestingConfig`)                                                                                                                                                                                                                                           |
| `public/shared_jobs_routes.py`                                                                                                     | Queue-aware flash messages, `queue_positions` / `queue_position` template context                                                                                                                                                                                                                      |
| `templates/_macros.html`, `jobs_templates/_list_table.html`, `base_details_public.html`, `admin_templates/base_details_admin.html` | `Queued · #N` status labels                                                                                                                                                                                                                                                                            |

## 4. Concurrency and atomic claiming

Claiming is a single conditional `UPDATE` inside one short transaction:

```sql
UPDATE jobs
   SET status = 'running', is_running = 1, started_at = NOW()
 WHERE id = :id AND status = 'pending' AND is_running IS NULL
```

- `rowcount == 0` → somebody else claimed it, or it is no longer pending.
- `IntegrityError` on `idx_unique_active_job` → another job of the same type
  holds the slot. Treated as a normal lost race (`claim_pending_job` returns
  `False`, the job stays queued).
- No lock is held while the job executes; the transaction ends at the claim.
- Bulk updates call `session.expire_all()` because the session is configured
  with `expire_on_commit=False`.

`dispatch_next()` retries with the next pending row (bounded by
`MAX_CLAIM_ATTEMPTS`) so one lost race or one bad job cannot stall the queue.

## 5. Durable payloads and identity

Persisted per job as `{job_type}_job_{id}.payload.json` in the existing jobs
directory:

```json
{ "args": { ... }, "form_data": { ... }, "username": "…" }
```

- `csrf_token`, `access_token`, `access_secret`, `password`, `secret` and
  `token` keys are stripped before writing (`sanitize_payload`).
- **No OAuth secret is ever written to the queue payload.** At dispatch time
  `JobIdentityResolver` reloads the _encrypted_ token through
  `TokenManager.get_auth_payload_by_username()` — the same shape produced by
  `CurrentUser.to_auth_payload()`, which `WikiSiteClient` decrypts.
- `Background job` (CLI/cron submissions) keeps using the tool bot password.
- If credentials disappeared, the job is failed with
  `User credentials are no longer available; please log in again` and the slot
  is released — nothing sensitive is logged.
- If payload persistence fails, the job is immediately marked `failed`
  (`Failed to store the job payload`) and never dispatched.

## 6. Cancellation race handling

`cancel_job_db()` marks a _running_ job `cancelled` but **keeps**
`is_running = 1`. The slot is released only by:

1. the worker's own terminal status update (`_update_job_status`), or
2. `thread_backend._runner`'s `finally` hook when the thread really exits, or
3. `JobsService.release_stale_active_slots()` during recovery, after
   `STALE_SLOT_GRACE_SECONDS` (300 s) — for executions that disappeared.

Therefore a queued job can never overlap a cancellation that is still winding
down. Queued jobs are cancelled through `cancel_pending_job()`, which only
matches `status='pending' AND is_running IS NULL`, so a job claimed in the
meantime is never cancelled by mistake.

## 7. Recovery

- **Startup:** `init_db()` runs the existing `cleanup_stale_jobs_on_startup()`
  (thread jobs cannot survive a restart) and then `JobsQueue.recover(force=True)`.
  Disabled under `TestingConfig` so tests never spawn worker threads while the
  app is built.
- **Periodic:** `flask dispatch-jobs` (`toolforge/shs/dispatch_jobs.sh`) can be
  scheduled like the existing `offline` cron job, e.g.
  `toolforge-jobs run queue-dispatcher --image python3.13 --command "~/shs/dispatch_jobs.sh"`.
  It is throttled and idempotent, so it is safe to run often and concurrently.
- Recovery never marks a running job failed just because a web process
  restarted; only slots of _terminal_ jobs older than the grace period, or
  thread jobs cleaned up by the pre-existing startup routine, are released.

## 8. Deployment order

1. Deploy the code (no schema change, no data backfill).
2. Optional: schedule `~/shs/dispatch_jobs.sh` for periodic recovery.
3. Rows created before the deploy keep working: a legacy `pending` row with
   `is_running = 1` is simply treated as holding the slot.

## 9. Out of scope (unchanged)

Redis/Celery, priorities, global concurrency limits, automatic retries of
failed jobs, and a separate queue dashboard — as listed in the plan.

## 10. Tests

```bash
pytest tests/unit/jobs_workers/jobs_lifetime          # queue + lifecycle
pytest tests/unit/database/services/test_jobs_service.py  # queue primitives
pytest tests/integration/admin/routes/test_jobs_queue_ui.py  # UI
pytest                                                 # full regression
```

Result at implementation time: **2955 passed, 2 skipped** (full suite).
