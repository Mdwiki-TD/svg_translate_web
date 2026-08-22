# Plan 003: Fix Python version mismatch in pyproject.toml

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 8bf215bc..HEAD -- pyproject.toml`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `8bf215bc`, 2025-08-11

## Why this matters

`pyproject.toml` declares `requires-python = ">=3.13"` but the actual runtime
(Toolforge and CI) uses Python 3.12. This means:

1. `pip install` would refuse to install on the production runtime if PEP 621
   enforcement kicks in (some installers reject mismatches).
2. Tool configs (`black`, `ruff`, `mypy`, `pyright`) all target Python 3.13,
   potentially flagging valid 3.12 code as errors or missing 3.12-specific issues.
3. The `AGENTS.md` says "Python 3.11+" which contradicts `pyproject.toml`.

## Current state

- `pyproject.toml:6` — `requires-python = ">=3.13"`
- `pyproject.toml:17` — `target-version = ["py313"]` (black)
- `pyproject.toml:50` — `target-version = "py313"` (ruff)
- `pyproject.toml:100` — `python_version = "3.13"` (mypy)
- `pyproject.toml:108` — `pythonVersion = "3.13"` (pyright)
- Runtime: Python 3.12.3
- `AGENTS.md` says: "Target version: Python 3.11+"

## Commands you will need

| Purpose     | Command                                     | Expected on success |
|-------------|---------------------------------------------|---------------------|
| Grep verify | `grep "3\.13" pyproject.toml`               | no matches          |
| Tests       | `python3 -m pytest tests/ -x -q -m "not network"` | all pass      |

## Scope

**In scope**:
- `pyproject.toml`

**Out of scope**:
- Any Python source code changes (do not downgrade 3.13-specific syntax — there likely isn't any)
- `AGENTS.md` (will be updated separately if needed)
- CI/CD configurations

## Steps

### Step 1: Update all Python version references to 3.12

In `pyproject.toml`, change all `3.13` references to `3.12`:

1. Line 6: `requires-python = ">=3.13"` → `requires-python = ">=3.12"`
2. Line 17: `target-version = ["py313"]` → `target-version = ["py312"]`
3. Line 50: `target-version = "py313"` → `target-version = "py312"`
4. Line 100: `python_version = "3.13"` → `python_version = "3.12"`
5. Line 108: `pythonVersion = "3.13"` → `pythonVersion = "3.12"`

**Verify**: `grep "3\.13" pyproject.toml` → no matches

### Step 2: Run the test suite to confirm nothing breaks

**Verify**: `python3 -m pytest tests/ -x -q -m "not network"` → all pass

### Step 3: Run ruff check (if available)

**Verify**: `python3 -m ruff check src/` → exits 0 (or only pre-existing warnings)

## Test plan

No new tests needed. This is a configuration-only change.

## Done criteria

- [ ] `grep "3\.13" pyproject.toml` returns no matches
- [ ] `grep "3\.12" pyproject.toml` returns at least 5 matches (one per tool)
- [ ] `python3 -m pytest tests/ -x -q -m "not network"` exits 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

- The version has already been updated to 3.12 or a different version.
- The runtime is actually Python 3.13+ (check `python3 --version` first).

## Maintenance notes

- When the Toolforge runtime upgrades to Python 3.13, bump all references in `pyproject.toml` at that time.
- `AGENTS.md` currently says "Python 3.11+" — consider updating it to "Python 3.12+" to match this change.
