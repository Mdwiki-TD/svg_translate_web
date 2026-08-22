# Plan 006: Replace custom in-memory rate limiter with flask-limiter

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 8bf215bc..HEAD -- src/main_app/public/auth/rate_limit.py src/main_app/public/auth/routes.py src/main_app/__init__.py`

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `8bf215bc`, 2025-08-11

## Why this matters

The current auth rate limiter (`rate_limit.py`) uses in-process Python dicts to
track request timestamps per client key. This has two production issues:

1. **Per-process isolation**: On Toolforge with gunicorn/uvicorn workers, each
   worker process has its own rate limit state. An attacker distributing requests
   across workers bypasses the limit entirely (5 req/min per worker × N workers).

2. **No persistence**: Rate limit state is lost on every restart, so an attacker
   can trigger a restart (or wait for a deploy) to reset their budget.

`flask-limiter` is already in `requirements.txt` but unused. It supports
services backends (Redis, Memcached) and falls back to in-memory for development.
Migrating to it fixes both issues and removes ~60 lines of custom code.

## Current state

- `src/main_app/public/auth/rate_limit.py` — custom `RateLimiter` class (lines 1-58)
  - `login_rate_limiter = RateLimiter(limit=5, period=timedelta(minutes=1))`
  - `callback_rate_limiter = RateLimiter(limit=10, period=timedelta(minutes=1))`

- `src/main_app/public/auth/routes.py` — uses the custom rate limiter
  - Line 42: `from .rate_limit import callback_rate_limiter, login_rate_limiter`
  - Lines 100-106: `login_rate_limiter.allow()` / `try_after()` in `login()`
  - Lines 131-134: `callback_rate_limiter.allow()` in `callback()`

- `src/main_app/__init__.py` — app factory, where `flask-limiter` needs initialization
- `requirements.txt` — already includes `flask-limiter`
- `src/main_app/config/flask_config.py` — Flask config classes

Repo convention: extensions are initialized in `src/main_app/extensions/__init__.py`
and initialized with the app via `ext.init_app(app)` in the factory.
See `src/main_app/extensions/_csrf.py` for the pattern.

## Commands you will need

| Purpose   | Command                                              | Expected on success |
|-----------|------------------------------------------------------|---------------------|
| Tests     | `python3 -m pytest tests/ -x -q -m "not network"`   | all pass            |
| Grep      | `grep -rn "RateLimiter" src/main_app/`               | only the flask-limiter usage, not the custom class |

## Scope

**In scope**:
- `src/main_app/public/auth/rate_limit.py` — replace custom class with flask-limiter wrapper
- `src/main_app/public/auth/routes.py` — update to use flask-limiter decorators or programmatic API
- `src/main_app/extensions/__init__.py` — add limiter initialization
- `src/main_app/extensions/_limiter.py` — new file for limiter extension
- `src/main_app/__init__.py` — initialize limiter in app factory
- `tests/` — update rate limiter tests

**Out of scope**:
- Any non-auth rate limiting (e.g., API endpoints) — that's a separate concern
- Redis/Memcached backend configuration — use in-memory for now; document how to switch to Redis later
- Changes to the rate limit values (5/min for login, 10/min for callback)

## Steps

### Step 1: Create the limiter extension

Create `src/main_app/extensions/_limiter.py`:

```python
"""Flask-Limiter extension initialization."""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

__all__ = ["limiter"]
```

**Verify**: `python3 -c "from src.main_app.extensions._limiter import limiter; print(type(limiter))"` → shows Limiter type

### Step 2: Export the limiter from extensions `__init__.py`

In `src/main_app/extensions/__init__.py`:

1. Add import: `from ._limiter import limiter`
2. Add `"limiter"` to `__all__`

**Verify**: `python3 -c "from src.main_app.extensions import limiter; print('ok')"` → prints "ok"

### Step 3: Initialize limiter in app factory

In `src/main_app/__init__.py`, inside `create_app()`:

1. Add import: `from .extensions import limiter`
2. After `csrf_init_app(app)`, add: `limiter.init_app(app)`

**Verify**: `grep -n "limiter.init_app" src/main_app/__init__.py` → one match

### Step 4: Replace custom rate limiter in `rate_limit.py`

Replace the entire contents of `src/main_app/public/auth/rate_limit.py`:

```python
"""Rate limiting for authentication endpoints using flask-limiter."""

from __future__ import annotations

from ...extensions import limiter

# Rate limit strings for flask-limiter
LOGIN_RATE_LIMIT = "5 per minute"
CALLBACK_RATE_LIMIT = "10 per minute"

__all__ = [
    "limiter",
    "LOGIN_RATE_LIMIT",
    "CALLBACK_RATE_LIMIT",
]
```

**Verify**: `grep -n "class RateLimiter" src/main_app/public/auth/rate_limit.py` → no matches

### Step 5: Update auth routes to use flask-limiter

In `src/main_app/public/auth/routes.py`:

1. Replace the import:
   - Remove: `from .rate_limit import callback_rate_limiter, login_rate_limiter`
   - Add: `from .rate_limit import CALLBACK_RATE_LIMIT, LOGIN_RATE_LIMIT, limiter`

2. In the `login()` method, replace the manual rate limit check (lines 99-108):

Before:
```python
if not login_rate_limiter.allow(_client_key()):
    time_left = login_rate_limiter.try_after(_client_key()).total_seconds()
    time_left_str = str(time_left).split(".")[0]
    flash(f"Too many login attempts. Please try again after {time_left_str}s.", "warning")
    logger.warning("OAuth login rate limited, client: %s, try_after: %ss", _client_key(), time_left_str)
    return redirect(
        url_for("main.index", error=f"Too many login attempts. Please try again after {time_left_str}s.")
    )
```

After: use `limiter.limit()` decorator on the method, OR use the programmatic
`limiter.check()` API. Since the current code does custom flash/redirect on
rate limit, use the decorator with a custom `on_breach` callback:

```python
@limiter.limit(LOGIN_RATE_LIMIT)
def login(self) -> WerkzeugResponse:
    logger.info("OAuth login initiated, client: %s", _client_key())
    # ... rest of login logic without the manual rate limit check
```

But flask-limiter's decorator approach requires wrapping the method directly.
Since `AuthRoutes._setup_routes` registers routes dynamically (not via decorators
on the class), the programmatic approach is cleaner:

Replace the manual check with:
```python
try:
    limiter.check(LOGIN_RATE_LIMIT)
except Exception:
    flash("Too many login attempts. Please try again later.", "warning")
    logger.warning("OAuth login rate limited, client: %s", _client_key())
    return redirect(url_for("main.index", error="Too many login attempts."))
```

3. Similarly in `callback()`, replace lines 131-134:

```python
try:
    limiter.check(CALLBACK_RATE_LIMIT)
except Exception:
    flash("Too many login attempts", "warning")
    logger.warning("OAuth callback rate limit exceeded, client: %s", _client_key())
    return redirect(url_for("main.index", error="Too many login attempts"))
```

4. Remove the `_client_key()` function if it's no longer needed for rate limiting
   (check if it's used in log messages — it is, so keep it).

**Verify**: `grep -n "login_rate_limiter\|callback_rate_limiter" src/main_app/public/auth/routes.py` → no matches

### Step 6: Run the test suite

**Verify**: `python3 -m pytest tests/ -x -q -m "not network"` → all pass

### Step 7: Add/update rate limiter tests

If existing tests test the custom `RateLimiter` class, remove those tests and
replace with tests that verify:
- Login endpoint returns 429 (or redirect with flash message) after 5 requests in 1 minute
- Callback endpoint returns 429 after 10 requests in 1 minute

**Verify**: `python3 -m pytest tests/ -x -q -m "not network" -k "rate"` → passes

## Test plan

- Remove any tests for the old custom `RateLimiter` class
- Add tests verifying flask-limiter enforcement on `/login` and `/callback`
- Model after existing auth integration tests in `tests/integration/public/auth/`
- Verification: `python3 -m pytest tests/ -x -q -m "not network"` → all pass

## Done criteria

- [ ] `grep -rn "class RateLimiter" src/main_app/` returns no matches
- [ ] `flask-limiter` is initialized in the app factory
- [ ] Auth routes use `limiter.check()` instead of custom rate limiter
- [ ] `python3 -m pytest tests/ -x -q -m "not network"` exits 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

- `flask-limiter` is not installable or not in `requirements.txt` (it IS listed — verify first).
- The `flask-limiter` API has changed significantly from what's described here — check `pip show flask-limiter` for the installed version.
- The auth routes have been refactored to a different pattern that doesn't use the `_setup_routes` method.

## Maintenance notes

- **Switching to Redis**: When deploying with multiple workers, change `storage_uri="memory://"` to `storage_uri="redis://localhost:6379"` (or use an env var). Add `RATELIMIT_STORAGE_URI` to `.env.example`.
- If the app adds rate limiting to more endpoints (API, file serving), use the same `limiter` instance.
- The `_client_key()` helper uses `X-Forwarded-For` which is correct for Toolforge's proxy setup. `flask-limiter`'s `get_remote_address` also handles this, but verify in production.
