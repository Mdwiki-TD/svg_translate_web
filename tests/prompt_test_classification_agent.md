You are a test classification agent. Your task is to analyze all test files under
`tests/main_app/` and classify them into the new test structure.

## Context

The project is reorganizing tests into three types:

1. **Unit Tests** (`tests/unit/`): Tests a single function/class in isolation

    - Uses mocks/patches for all external dependencies (DB, HTTP, filesystem)
    - No real Flask app context, no real DB connections
    - Fast, no I/O

2. **Integration Tests** (`tests/integration/`): Tests interaction between 2–3 components

    - May use a real in-memory DB (e.g. SQLite fixture) or Flask test client
    - Tests that a service correctly calls the DB layer, or that a route correctly
      calls a service — but not the full user-facing flow

3. **Functional Tests** (`tests/functional/`): Tests a complete user-facing flow end-to-end
    - Uses Flask test client + real routes + real DB together
    - Simulates what a real user/browser would do

## Path Mirroring Rule

Every test file **must mirror** its `src/main_app/` counterpart path. Examples:

-   `src/main_app/db/db_Jobs.py` → `tests/unit/main_app/db/test_db_Jobs.py`
-   `src/main_app/app_routes/auth/routes.py` → `tests/integration/main_app/app_routes/auth/test_routes.py`
-   `src/main_app/services/jobs_service.py` → `tests/unit/main_app/services/test_jobs_service.py`

## Split File Naming Convention

If a file contains tests of two different types (e.g. unit + integration),
it must be split into two files using this naming pattern:

```
test_store.py        ← integration half
test_store_unit.py   ← unit half
```

## Your Task

For **every file** listed in the scope below:

1. **Read the file** and analyze each test function
2. **Classify each test** as `unit`, `integration`, or `functional`
3. **Determine the action**:
    - `MOVE_ONLY` — all tests are the same type, just move the file
    - `SPLIT` — tests are mixed types, file must be split into two files
    - `DELETE` — file is empty or a placeholder (delete after review)

## Classification Signals

| Signal in test code                                  | Type        |
| ---------------------------------------------------- | ----------- |
| `MagicMock()`, `patch()`, `monkeypatch` on DB/HTTP   | unit        |
| `@pytest.mark.unit`                                  | unit        |
| Tests a single pure function (no I/O)                | unit        |
| Uses a real SQLite fixture or in-memory DB           | integration |
| Uses `app.test_client()` to call a route             | integration |
| Tests service calling DB layer with real objects     | integration |
| Full flow: login → action → DB check via test client | functional  |
| `@pytest.mark.functional`                            | functional  |

## Scope — Files to Analyze

Analyze **only** the following files (read each one before classifying):

-   all python files under `tests/main_app/`

## Important Notes

-   **Do NOT skip any file** — read and classify every file listed above
-   **Skip** `conftest.py` files
-   **Skip** files already under `tests/unit/`, `tests/integration/`, `tests/functional/`
-   When a file path under `tests/main_app/users/` has no matching `src/main_app/users/` module,
    trace the import in the test file to find the real source module and mirror that path instead
-   For `SPLIT` files: list which exact test function names go to each destination

## Output Format

Return a Markdown report saved to `plans/test_classification_report_main_app.md` with:

1. **Summary Statistics**

    - Total files analyzed
    - Files MOVE_ONLY → unit
    - Files MOVE_ONLY → integration
    - Files MOVE_ONLY → functional
    - Files to SPLIT
    - Files to DELETE

2. **Detailed Classification Table**

| File                                | Type  | Action | Tests Count | Destination              |
| ----------------------------------- | ----- | ------ | ----------- | ------------------------ |
| `tests/main_app/db/test_db_Jobs.py` | mixed | SPLIT  | 6           | unit(4) + integration(2) |

3. **Files Requiring Split** (detailed breakdown per file)

    - Source file
    - Which test functions → unit destination
    - Which test functions → integration destination

4. **Git Commands** (ready-to-execute)

```bash
# Move files (MOVE_ONLY)
git mv tests/main_app/old/path.py tests/unit/main_app/new/path.py

# Split files — create new files, then delete old
# (list each split file with its two destination paths)
```

Start by reading the files one by one. Be thorough and accurate.
