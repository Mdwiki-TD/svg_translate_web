# Test Suite Documentation

This directory contains unit and integration tests for the project using the **pytest** framework.

## When to Mock in Flask-SQLAlchemy Tests

### Why mocking the ORM is usually a mistake

-   **You end up testing your mocks, not your code.** When you stub out `db.session` or model classes to return canned objects, you're verifying that your mock framework behaves as configured — not that your SQL, your queries, or your business logic actually work.
-   **Mocks can't catch real database behavior.** Constraint violations, trigger side effects, malformed SQL in complex queries, transaction rollback behavior, schema mismatches — none of this surfaces through a mock. The test passes green while the real query would fail in production.
-   **Mocked tests are brittle under refactoring.** Tweak a query for performance or change how you fetch a relationship, and the mock setup breaks even though the underlying behavior is unchanged — meaning you spend more time maintaining test scaffolding than the actual feature.
-   **It violates "don't mock what you don't own."** SQLAlchemy is a third-party library with its own internal state machine (identity map, unit of work, session lifecycle). Trying to hand-simulate that state machine in a mock is a losing battle — you'll never fully replicate it, and partial replication is where subtle bugs hide.

### Default rule

If a real test database is available (SQLite in-memory, test Postgres, etc.) with proper teardown/rollback between tests, **prefer real DB operations over mocking**.

### ✅ DO mock / patch / MagicMock

-   **External network calls**: third-party APIs, payment gateways (Stripe, PayPal), SMS/email providers (SendGrid, Twilio), webhooks.
-   **File/object storage**: S3, GCS, local filesystem writes you don't want littering disk during tests.
-   **Non-deterministic values you need fixed**: `datetime.utcnow()`, `uuid.uuid4()`, `random`, when the test asserts on an exact value.
-   **`time.sleep` (and equivalents: `asyncio.sleep`, `threading.Event().wait(timeout=...)`, any busy-wait)** — always mock this. It adds no test value and just slows the suite, especially with retry/backoff logic (e.g. exponential backoff of 1s, 2s, 4s...). Mock it so you can assert on `call_count` without actually waiting.
-   **Slow/expensive operations** you deliberately isolate: password hashing rounds (bcrypt), image processing, PDF generation, ML model inference.
-   **Hard-to-trigger error paths**: simulating `OperationalError`, `IntegrityError`, connection drops, timeouts — patch the session method to raise, rather than trying to force a real DB into that state.
-   **Third-party SDKs / clients** injected into your service (e.g., a Redis client, a Celery task dispatcher, a message queue producer) — mock the client, not your own code.
-   **Time-based scheduling / background jobs** — mock the scheduler/task queue trigger, not the DB write it eventually causes.
-   **Feature flags / external config services** (LaunchDarkly, etc.).
-   **Auth/identity providers** (OAuth callbacks, JWT verification against a remote JWKS endpoint) — mock the external verification call itself, not your local token logic.

### ❌ DON'T mock

-   `db.session.add`, `db.session.commit`, `db.session.query`, `db.session.delete` — just use the real test session.
-   Model classes (`User`, `Admin`, etc.) — create real rows via a factory/fixture.
-   Your own repository/service methods calling each other within the same test DB — call them for real; that's what proves integration works.
-   SQLAlchemy relationships, cascades, or constraints (unique, FK, not-null) — test against the real schema; mocking hides exactly the bugs these exist to catch.
-   Query results (`.filter_by().first()`, `.all()`) — seed real data and query it for real.
-   **Retry configuration values** (`max_attempts`, `backoff_factor`, etc.) — don't mock these. Either pass a small explicit value for the test (e.g. `max_attempts=2`) or test the hardcoded default as-is; just mock `time.sleep` so retries don't actually wait.

### Quick test

Before adding a mock, ask: **"Does this cross a boundary outside my own database/process, or is it a real-time delay?"**

-   Yes → mock is justified.
-   No (it's just my own DB read/write, or a config value) → don't mock it, use the real thing.

## Test Organization

To maintain clean code and readability, tests are **grouped into test classes (`Test Classes`)** based on the module, method, or feature under test (e.g., `Test<FeatureName>`).

#### Guidelines & Best Practices:

1. **Class Naming:** Test classes must start with `Test` using PascalCase (e.g., `TestValidateProjectConfig`).
2. **Docstrings:** Include a brief docstring for every test class describing the purpose of the contained tests.
3. **Fixtures & Mocking:** Isolate tests from external I/O (network, database, file system) using `pytest.fixture` and `unittest.mock`.
4. **Test Naming:** Test methods must start with `test_` and clearly describe the scenario being verified.

---

### Standard Test File Structure

Every test module follows a consistent structure divided by clear section headers:

1. **Setup & Fixtures:** Global fixtures, mocks, and helper functions.
2. **Test Classes:** Isolated classes for each target method or component.

#### Example Pattern:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock


# ---------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------
@pytest.fixture
def updater(tmp_path, monkeypatch):
    """Create a configured `ReportUpdater` and mocked repository for testing."""
    repo = MagicMock()
    # ... mock setup ...
    return updater_instance, repo


# ---------------------------------------------------------------
# 1. Tests for validate_project_config
# ---------------------------------------------------------------
class TestValidateProjectConfig:
    """Tests for the `validate_project_config` method of the `ReportUpdater` class."""

    def test_validate_project_config_valid(self, updater):
        u, repo = updater
        repo.does_title_exist.return_value = True
        assert u.validate_project_config("Wikipedia:WikiProject Foo", _project()) is True

    def test_validate_project_config_rejects_missing_project_page(self, updater):
        u, repo = updater
        repo.does_title_exist.return_value = False
        assert u.validate_project_config("Wikipedia:WikiProject Foo", _project()) is False


# ---------------------------------------------------------------
# 2. Tests for process_project (Async)
# ---------------------------------------------------------------
class TestProcessProject:
    """Tests for the `process_project` method of the `ReportUpdater` class."""

    @pytest.mark.asyncio
    async def test_process_project_renders_report_from_cache(self, updater):
        u, repo = updater
        # ... test execution ...
        assert "Expected Content" in written_text


# ---------------------------------------------------------------
# 3. Pipeline & Index Tests
# ---------------------------------------------------------------
class TestUpdateReports:
    """Tests for the `update_reports` method of the `ReportUpdater` class."""

    ...


class TestUpdateIndex:
    """Tests for the `update_index` method of the `ReportUpdater` class."""

    ...
```
