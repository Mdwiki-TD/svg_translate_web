# Plan 005: Deduplicate job stats query methods in JobsService

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 8bf215bc..HEAD -- src/main_app/database/services/jobs_service.py`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `8bf215bc`, 2025-08-11

## Why this matters

`JobsService` has two methods that compute user job statistics:
`get_user_jobs_stats` (lines 68-120) and `_get_all_user_jobs_stats` (lines 270-302).
They share ~80% identical code: both build a `base_query`, run a `group_by` status
count query, fetch recent jobs, compute `status_counts`, and assemble the same
`{"stats": ..., "recent_jobs": ...}` dict. The only difference is that
`get_user_jobs_stats` optionally filters by `jobs_types`. This duplication means
any bug fix or feature change must be made in two places, and the existing
divergence (one uses `.in_()` filter, the other doesn't) is a maintenance hazard.

## Current state

- `src/main_app/database/services/jobs_service.py` — JobsService class
  - Lines 68-120: `get_user_jobs_stats` — takes optional `jobs_types` list, falls back to `_get_all_user_jobs_stats`
  - Lines 270-302: `_get_all_user_jobs_stats` — same logic without the `jobs_types` filter
  - Line 58: `get_all_user_jobs_stats` — public wrapper that calls `_get_all_user_jobs_stats`

The relationship: `get_user_jobs_stats` already delegates to `_get_all_user_jobs_stats`
when `jobs_types` is None/empty (line 79). So the fix is to fold `_get_all_user_jobs_stats`
into `get_user_jobs_stats` and make `get_all_user_jobs_stats` call `get_user_jobs_stats`
with no filter.

Repo convention: services use `CRUDService[ModelT]` base class. Method names
follow `snake_case`. Private methods prefixed with `_`.

## Commands you will need

| Purpose   | Command                                              | Expected on success |
|-----------|------------------------------------------------------|---------------------|
| Tests     | `python3 -m pytest tests/unit/database/ -x -q -m "not network"` | all pass       |
| Grep      | `grep -n "_get_all_user_jobs_stats" src/main_app/database/services/jobs_service.py` | 0 matches (or only the delegate call) |

## Scope

**In scope**:
- `src/main_app/database/services/jobs_service.py`

**Out of scope**:
- Any callers of `get_all_user_jobs_stats` or `get_user_jobs_stats` (the public API signature must not change)
- Any test files (unless they test internal private methods that are being removed)

## Steps

### Step 1: Consolidate `_get_all_user_jobs_stats` into `get_user_jobs_stats`

In `src/main_app/database/services/jobs_service.py`:

1. Replace the body of `get_user_jobs_stats` (lines 68-120) so it no longer
   delegates to `_get_all_user_jobs_stats` when `jobs_types` is None. Instead,
   handle both cases inline:

```python
def get_user_jobs_stats(
    self,
    username: str,
    jobs_types: list | None = None,
    limit: int | None = 100,
) -> dict[str, dict[str, int] | list[JobRecord]]:
    """Get user job statistics, optionally filtered by job types."""
    limit = _normalize_limit(limit)

    base_query = self.session.query(JobRecord).filter(JobRecord.username == username)

    status_query = (
        self.session.query(JobRecord.status, func.count(JobRecord.id))
        .filter(JobRecord.username == username)
    )

    if jobs_types:
        base_query = base_query.filter(JobRecord.job_type.in_(jobs_types))
        status_query = status_query.filter(JobRecord.job_type.in_(jobs_types))

    records = status_query.group_by(JobRecord.status).all()
    status_counts: dict[str, int] = {row[0]: row[1] for row in records}

    recent_jobs = base_query.order_by(JobRecord.created_at.desc()).limit(limit).all()

    total_jobs = sum(status_counts.values())

    stats: dict[str, int] = {
        "total": total_jobs,
        "completed": status_counts.get("completed", 0),
        "failed": status_counts.get("failed", 0),
        "cancelled": status_counts.get("cancelled", 0),
    }

    return {
        "stats": stats,
        "recent_jobs": recent_jobs,
    }
```

2. Update `get_all_user_jobs_stats` to delegate to the consolidated method:

```python
def get_all_user_jobs_stats(
    self,
    username: str,
    limit: int | None = 100,
) -> dict[str, dict[str, int] | list[JobRecord]]:
    return self.get_user_jobs_stats(username, jobs_types=None, limit=limit)
```

3. Delete `_get_all_user_jobs_stats` entirely (lines 270-302).

**Verify**: `grep -n "_get_all_user_jobs_stats" src/main_app/database/services/jobs_service.py` → no matches

### Step 2: Run the test suite

**Verify**: `python3 -m pytest tests/unit/database/ -x -q -m "not network"` → all pass

### Step 3: Run the full test suite

**Verify**: `python3 -m pytest tests/ -x -q -m "not network"` → all pass

## Test plan

No new tests needed. The existing tests for `JobsService` exercise the public methods
`get_all_user_jobs_stats` and `get_user_jobs_stats`, which maintain the same interface.

## Done criteria

- [ ] `grep -n "_get_all_user_jobs_stats" src/main_app/database/services/jobs_service.py` returns no matches
- [ ] `get_user_jobs_stats` handles both filtered and unfiltered cases
- [ ] `get_all_user_jobs_stats` delegates to `get_user_jobs_stats`
- [ ] `python3 -m pytest tests/ -x -q -m "not network"` exits 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

- The `_get_all_user_jobs_stats` method has already been removed.
- A caller directly references `_get_all_user_jobs_stats` (private method) — search with `grep -rn "_get_all_user_jobs_stats" src/ tests/` before deleting.
- The `get_user_jobs_stats` signature has changed since this plan was written.

## Maintenance notes

- If new filter dimensions are needed (e.g., date range), add them as optional parameters to `get_user_jobs_stats` rather than creating another method.
- The `stats` dict intentionally omits `running` and `pending` counts (commented out in the original). If those are needed later, add them to the consolidated method.
