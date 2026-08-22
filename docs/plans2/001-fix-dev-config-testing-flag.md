# Plan 001: Remove `TESTING = True` from DevelopmentConfig

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 8bf215bc..HEAD -- src/main_app/config/flask_config.py`
> If the file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `8bf215bc`, 2025-08-11

## Why this matters

`DevelopmentConfig` currently sets `TESTING = True`, which causes Flask to disable
error handlers, propagate exceptions instead of rendering error pages, and disable
CSRF protection in some configurations. If the app is accidentally deployed with
`FLASK_ENV=development` (which is the default in `.env.example`), this effectively
disables production safety nets. The `TestingConfig` subclass already exists and
is the correct place for `TESTING = True`.

## Current state

- `src/main_app/config/flask_config.py` — Flask configuration classes
  - Line 114-127: `DevelopmentConfig` class with `TESTING: bool = True` on line 117

```python
# src/main_app/config/flask_config.py:114-127
class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""

    DEBUG: bool = True
    TESTING: bool = True          # <-- THIS IS THE PROBLEM
    SQLALCHEMY_ECHO: bool = False

    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    CORS_DISABLED: bool = True
```

The repo convention is: `Config` is the base, `DevelopmentConfig` for local dev,
`ProductionConfig` for production, `TestingConfig` for tests. Only `TestingConfig`
should have `TESTING = True`.

## Commands you will need

| Purpose   | Command                                    | Expected on success                |
|-----------|--------------------------------------------|------------------------------------|
| Tests     | `python3 -m pytest tests/ -x -q`          | all pass                           |
| Grep      | `grep -n "TESTING" src/main_app/config/flask_config.py` | Only `TestingConfig` has `True` |

## Scope

**In scope** (the only files you should modify):
- `src/main_app/config/flask_config.py`

**Out of scope** (do NOT touch):
- `TestingConfig` — already correct
- `ProductionConfig` — already correct
- Any test files

## Steps

### Step 1: Remove `TESTING = True` from `DevelopmentConfig`

In `src/main_app/config/flask_config.py`, change line 117 from:

```python
    TESTING: bool = True
```

to:

```python
    TESTING: bool = False
```

**Verify**: `grep -n "TESTING" src/main_app/config/flask_config.py` → only `TestingConfig` shows `TESTING: bool = True`

### Step 2: Run the test suite

**Verify**: `python3 -m pytest tests/ -x -q` → all pass (no test should depend on `DevelopmentConfig.TESTING` being True)

## Test plan

No new tests needed. Existing tests use `TestingConfig`, not `DevelopmentConfig`.

## Done criteria

- [ ] `grep -n "TESTING.*True" src/main_app/config/flask_config.py` returns only the `TestingConfig` line
- [ ] `python3 -m pytest tests/ -x -q` exits 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

- The `DevelopmentConfig` class no longer contains `TESTING: bool = True` (already fixed by someone else).
- A test fails that specifically asserts `DevelopmentConfig.TESTING is True` — report back, this needs investigation.

## Maintenance notes

- If any developer workflow relied on `TESTING = True` in development (e.g., bypassing CSRF), that workflow should use a dedicated dev-only setting instead.
