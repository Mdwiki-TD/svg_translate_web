# Plan 002: Protect API endpoints and unpublished chart data

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 8bf215bc..HEAD -- src/main_app/public/api_routes.py src/main_app/public/main_routes/owid_charts_routes.py`
> If either file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `8bf215bc`, 2025-08-11

## Why this matters

Two unauthenticated endpoints expose data that should be restricted:

1. **`/api/` routes** (`api_routes.py`) — expose template metadata, chart data, and
   view statistics with no authentication. While some of this data may be public
   (it originates from Wikimedia Commons), the aggregated internal structure
   (template relationships, unpublished chart metadata) is operational data.

2. **`/owidcharts/all`** (`owid_charts_routes.py`) — displays ALL charts including
   unpublished ones. The `/owidcharts/` index route correctly filters to
   `is_published`, but the `/all` route bypasses this filter.

## Current state

- `src/main_app/public/api_routes.py` — API endpoints, no auth decorators
  - Lines 18-20: `templates_list`, `templates_mismatched_years_list`, `templates_need_update_list` — no auth
  - Lines 22-23: `owid_charts_list` — no auth

- `src/main_app/public/main_routes/owid_charts_routes.py` — chart listing routes
  - Lines 35-38: `index()` filters `if x.chart.is_published` — correct
  - Lines 40-44: `all_charts()` returns ALL charts with no filter and no auth

- `src/main_app/public/auth/utils.py` — provides `user_login_required` and `oauth_required` decorators
- `src/main_app/admin/decorators.py` — provides `admin_required` decorator

Repo convention for auth: routes use `user_login_required` for logged-in users,
`admin_required` for admin-only, `oauth_required` for routes needing full OAuth tokens.
See `src/main_app/public/public_jobs.py:38-42` for an exemplar of the pattern.

## Commands you will need

| Purpose   | Command                                                | Expected on success |
|-----------|--------------------------------------------------------|---------------------|
| Tests     | `python3 -m pytest tests/ -x -q -m "not network"`     | all pass            |
| Grep auth | `grep -n "admin_required\|user_login_required" src/main_app/public/api_routes.py` | decorators present |

## Scope

**In scope** (the only files you should modify):
- `src/main_app/public/api_routes.py`
- `src/main_app/public/main_routes/owid_charts_routes.py`
- `tests/integration/` (new or updated tests for auth enforcement)

**Out of scope** (do NOT touch):
- The admin OWID charts routes (they already use `admin_required`)
- Any changes to the data returned by the API endpoints
- The `public_jobs.py` routes

## Steps

### Step 1: Add `admin_required` to `/owidcharts/all` route

In `src/main_app/public/main_routes/owid_charts_routes.py`:

1. Add import: `from ...admin.decorators import admin_required`
2. Add `admin_required` decorator to the `all_charts` method.

The `_setup_routes` method at line 27-30 currently registers routes as tuples:
```python
routes = [
    ("/", "GET", self.index),
    ("/all", "GET", self.all_charts),
]
```

Change the `/all` registration to wrap with `admin_required`:
```python
routes = [
    ("/", "GET", self.index),
    ("/all", "GET", admin_required(self.all_charts)),
]
```

**Verify**: `grep -n "admin_required" src/main_app/public/main_routes/owid_charts_routes.py` → import and usage both present

### Step 2: Add `user_login_required` to API template endpoints

In `src/main_app/public/api_routes.py`:

1. Add import: `from .auth.utils import user_login_required`
2. Wrap the three template endpoints with `user_login_required`:

```python
def _setup_routes(self) -> None:
    self.bp.get("/templates")(user_login_required(self.templates_list))
    self.bp.get("/templates-mismatched-years")(user_login_required(self.templates_mismatched_years_list))
    self.bp.get("/templates-need-update")(user_login_required(self.templates_need_update_list))

    self.bp.get("/owidcharts/")(self.owid_charts_list)
    self.bp.get("/owidcharts/<string:template_filter>")(self.owid_charts_list)
```

The OWID charts API endpoints (`/api/owidcharts/`) remain public because they serve published chart data. The template endpoints require login because they expose internal operational metadata.

**Verify**: `grep -n "user_login_required" src/main_app/public/api_routes.py` → import and three usages present

### Step 3: Run the test suite

**Verify**: `python3 -m pytest tests/ -x -q -m "not network"` → all pass

### Step 4: Add tests for auth enforcement

Create or update integration tests to verify:
- `GET /api/templates` returns 302 (redirect to login) when unauthenticated
- `GET /owidcharts/all` returns 302 (redirect to login) when unauthenticated
- `GET /api/owidcharts/` still works without authentication (public data)

Model after `tests/integration/public/main_routes/test_owid_charts_routes_integration.py`.

**Verify**: `python3 -m pytest tests/integration/public/ -x -q -m "not network"` → all pass including new tests

## Test plan

- New test: unauthenticated GET to `/api/templates` → 302 redirect
- New test: unauthenticated GET to `/owidcharts/all` → 302 redirect
- New test: unauthenticated GET to `/api/owidcharts/` → 200 OK (public)
- Pattern: model after existing integration tests in `tests/integration/public/main_routes/`

## Done criteria

- [ ] `GET /owidcharts/all` requires admin authentication (redirects for non-admin users)
- [ ] `GET /api/templates` requires user authentication (redirects for anonymous users)
- [ ] `GET /api/owidcharts/` remains publicly accessible
- [ ] `python3 -m pytest tests/ -x -q -m "not network"` exits 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

- The API routes already have auth decorators (someone else fixed this).
- Adding auth decorators breaks a downstream integration that depends on unauthenticated API access — report back instead of removing the decorator.
- The `admin_required` import path has changed.

## Maintenance notes

- If a public API is needed in the future, create a separate blueprint with explicit API key or token auth rather than removing these decorators.
- The OWID charts public endpoints should be monitored — if they start exposing non-public data, add auth.
