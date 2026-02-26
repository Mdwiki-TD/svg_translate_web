# MySQL Error 1203 Resolution: SQLAlchemy Connection Pooling Architecture

## Improved Version v2.0 — All Identified Weaknesses Addressed

---

> ### Summary of Improvements Over v1.0
>
> | #   | Weakness                                          | Fix Applied                                        |
> | --- | ------------------------------------------------- | -------------------------------------------------- |
> | 1   | Connection math exceeded MySQL limit (134 > 100)  | Reduced `max_overflow` — peak is now 88            |
> | 2   | Password embedded in f-string URL (encoding bugs) | Replaced with `URL.create()`                       |
> | 3   | No thread-safety on engine initialization         | Added `threading.Lock` with double-checked locking |
> | 4   | `get_connection` always commits (even on SELECT)  | Added `readonly=True` parameter                    |
> | 5   | Error 1203 raised immediately with no retry       | Added exponential backoff retry for 1203           |

---

## 1. Root Cause Analysis

### 1.1 Current Architecture Problems

| Issue                                   | Description                                               | Impact                                                                      |
| --------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- |
| **No Connection Pooling**               | Each `Database` instance creates a new PyMySQL connection | Connection count grows linearly with concurrent operations                  |
| **Global Singleton Pattern**            | `svg_db.py` caches a single `Database` instance globally  | All threads share one connection; concurrent access creates race conditions |
| **Connection-per-Request Anti-Pattern** | Each request may create multiple connections              | Rapid connection churn under load                                           |
| **No Connection Limit Enforcement**     | No upper bound on simultaneous connections                | Easily exceeds MySQL `max_user_connections` limit                           |
| **Background Task Isolation**           | Workers in `jobs_workers/` create independent connections | Multiplies connection count by worker threads                               |

### 1.2 Connection Count Analysis (Current State)

Given the deployment configuration:

```yaml
replicas: 2
cpu: 3
```

Assuming Gunicorn with `workers = 2 * CPU + 1 = 7` per pod:

| Component                             | Connections per Instance        | Total                |
| ------------------------------------- | ------------------------------- | -------------------- |
| Gunicorn workers (7 per pod × 2 pods) | 1 cached connection per worker  | 14                   |
| Background job workers                | 1–2 connections per worker      | 10–50+               |
| Batch processing (700 files)          | 1 connection per file operation | 700+                 |
| **Total Peak**                        | —                               | **750+ connections** |

With a typical Toolforge MySQL limit of `max_user_connections = 100`, this architecture will consistently fail under load.

---

## 2. Architectural Solution

### 2.1 SQLAlchemy Engine with Connection Pooling

Replace the raw PyMySQL implementation with SQLAlchemy's Engine, which provides:

-   **Connection Pooling** — Reuses connections across requests
-   **Pool Size Management** — Enforces upper bounds on concurrent connections
-   **Overflow Control** — Temporary connections for burst traffic
-   **Connection Validation** — `pool_pre_ping` detects stale connections
-   **Automatic Recycling** — `pool_recycle` prevents timeout errors

### 2.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Flask Application                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌───────────┐  ┌─────────────┐  │
│  │ HTTP Routes│  │  Background  │  │   Batch   │  │  Admin/CLI  │  │
│  │            │  │    Tasks     │  │  Workers  │  │  Commands   │  │
│  └─────┬──────┘  └──────┬───────┘  └─────┬─────┘  └──────┬──────┘  │
│        │                │               │               │           │
│        └────────────────┴───────────────┴───────────────┘           │
│                                  │                                   │
│                    ┌─────────────┴─────────────┐                    │
│                    │  HTTP Engine  │  BG Engine  │                   │
│                    │  pool_size=3  │  pool_size=4│                   │
│                    │  overflow=1   │  overflow=0 │                   │
│                    └─────────────┬─────────────┘                    │
│                                  │                                   │
│                    ┌─────────────▼─────────────┐                    │
│                    │       PyMySQL Driver        │                   │
│                    └─────────────┬─────────────┘                    │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  MySQL/Toolforge │
                          │  max_conn = 100  │
                          └─────────────────┘
```

---

## 3. Pool Configuration Strategy (Fixed)

### 3.1 Pool Parameters

| Parameter       | Description                              | Value                | Rationale                                           |
| --------------- | ---------------------------------------- | -------------------- | --------------------------------------------------- |
| `pool_size`     | Permanent connections in pool            | 3 (HTTP) / 4 (BG)    | Balance between readiness and resource usage        |
| `max_overflow`  | Temporary connections beyond pool_size   | 1 (HTTP) / 0 (BG)    | **Reduced from original** to stay under MySQL limit |
| `pool_recycle`  | Seconds before connection is recycled    | 3600                 | Prevent MySQL `wait_timeout` disconnections         |
| `pool_pre_ping` | Validate connection before use           | `True`               | Detect and replace stale connections                |
| `pool_timeout`  | Seconds to wait for available connection | 30                   | Fail fast instead of hanging indefinitely           |
| `echo`          | Log all SQL statements                   | `False` (production) | Enable only for debugging                           |

### 3.2 Connection Count Formula (Corrected)

```python
# Given:
# MySQL max_user_connections = M = 100
# Gunicorn workers per pod   = W = 7
# Number of pods/replicas    = R = 2
# Background worker threads  = B = 4

# Reserve 20% for admin operations and emergency headroom
available_connections = M * 0.80                               # = 80

# HTTP workers receive 60% of available connections
http_pool_allocation = available_connections * 0.60            # = 48
pool_size    = floor(http_pool_allocation / (W * R))           # = floor(48/14) = 3
max_overflow = 1   # Reduced from 2 to 1 to stay within budget

# Background workers receive 40% of available connections
bg_pool_allocation = available_connections * 0.40              # = 32
bg_pool_size       = floor(bg_pool_allocation / (B * R))       # = floor(32/8) = 4
bg_max_overflow    = 0   # No overflow for background — fixed pool only

# ─── Verification (must be <= 100) ─────────────────────────────────────
# HTTP:       7 workers x 2 pods x (3 pool + 1 overflow) =  56
# Background: 4 threads x 2 pods x (4 pool + 0 overflow) =  32
# Admin/other (the reserved 20%)                          =  12
# Peak total:  56 + 32 = 88  OK — 12-connection safety margin preserved
```

### 3.3 Toolforge-Specific Configuration

```python
# HTTP Worker Engine — optimized for short-lived web requests
HTTP_ENGINE_CONFIG = {
    "pool_size":     3,     # 3 permanent connections per worker
    "max_overflow":  1,     # 1 temporary connection for burst (reduced from 2)
    "pool_recycle":  3600,  # Recycle connections after 1 hour
    "pool_pre_ping": True,  # Validate before use
    "pool_timeout":  30,    # Raise after 30s wait — fail fast
}

# Background Worker Engine — optimized for sustained batch throughput
BACKGROUND_ENGINE_CONFIG = {
    "pool_size":     4,     # 4 permanent connections shared across threads
    "max_overflow":  0,     # No overflow — fixed pool prevents budget overrun
    "pool_recycle":  3600,
    "pool_pre_ping": True,
    "pool_timeout":  60,    # Longer timeout acceptable for batch operations
}

# ─── Connection Budget Summary ─────────────────────────────────────────────
# HTTP:        7 workers x 2 pods x (3 + 1) =  56 connections
# Background:  4 threads x 2 pods x (4 + 0) =  32 connections
# Peak total:  88 / 100  OK — 12-connection safety margin preserved
```

### 3.4 Configuration Matrix

| Environment | Workers | Pods | pool_size | max_overflow | Peak Connections |
| ----------- | ------- | ---- | --------- | ------------ | ---------------- |
| Local Dev   | 1       | 1    | 5         | 2            | 7                |
| Staging     | 3       | 1    | 3         | 1            | 12               |
| Production  | 7       | 2    | 3         | 1            | 56               |
| Background  | 4       | 2    | 4         | 0            | 32               |

---

## 4. Flask Integration

### 4.1 Engine Factory Module (Fully Improved)

`src/main_app/db/engine_factory.py`

```python
"""
SQLAlchemy Engine factory for connection pooling.

Improvements over v1.0:
  - URL.create()       : safe password encoding, no f-string interpolation
  - threading.Lock     : prevent double-initialization in multi-threaded envs
  - readonly parameter : skip commit() on SELECT-only connections
  - 1203 retry backoff : wait for pool to free up instead of raising immediately
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from ..config import DbConfig, settings

logger = logging.getLogger(__name__)

# ── Global singleton engines ────────────────────────────────────────────────
_http_engine:       Engine | None = None
_background_engine: Engine | None = None

# ── Thread-safety locks ─────────────────────────────────────────────────────
# Fix: the original code had no locking.
# Without these locks, two threads starting simultaneously could both see
# `_http_engine is None` and each create a separate engine, doubling the
# connection count before either assignment completes.
_http_engine_lock       = threading.Lock()
_background_engine_lock = threading.Lock()


class DatabaseError(Exception):
    """Wrapper for database-related errors."""
    pass


def _build_connection_url(db_config: DbConfig) -> URL:
    """
    Build a SQLAlchemy URL using URL.create() instead of an f-string.

    Fix: f-strings silently produce malformed URLs when passwords contain
    special characters such as @, #, %, &, or spaces.  URL.create()
    percent-encodes the password automatically — no manual escaping needed.
    """
    return URL.create(
        drivername="mysql+pymysql",
        username=db_config.db_user,
        password=db_config.db_password,   # encoded automatically by SQLAlchemy
        host=db_config.db_host,
        database=db_config.db_name,
        query={"charset": "utf8mb4"},
    )


def create_http_engine(db_config: DbConfig | None = None) -> Engine:
    """
    Create the HTTP-optimized engine (one per process, thread-safe).

    Uses double-checked locking:
      1. Fast path  : return immediately if already initialized.
      2. Acquire lock, check again, then create — exactly one thread wins.
    """
    global _http_engine

    # Fast path — no lock needed for reads after initialization
    if _http_engine is not None:
        return _http_engine

    with _http_engine_lock:
        # Second check inside the lock: another thread may have created
        # the engine while we were waiting to acquire the lock.
        if _http_engine is not None:
            return _http_engine

        config = db_config or settings.database_data

        _http_engine = create_engine(
            _build_connection_url(config),
            poolclass=QueuePool,
            pool_size=3,
            max_overflow=1,        # reduced from 2 to 1 to stay within budget
            pool_recycle=3600,
            pool_pre_ping=True,    # replace stale connections transparently
            pool_timeout=30,       # raise TimeoutError after 30 s
            echo=False,
            connect_args={
                "connect_timeout": 5,
                "read_timeout":    30,
                "write_timeout":   30,
                "init_command":    "SET time_zone = '+00:00'",
            },
        )

        logger.info(
            "event=http_engine_created pool_size=3 max_overflow=1 pool_recycle=3600"
        )
        return _http_engine


def create_background_engine(db_config: DbConfig | None = None) -> Engine:
    """
    Create the background-optimized engine (one per process, thread-safe).

    Uses the same double-checked locking pattern as create_http_engine.
    max_overflow=0 ensures background workers cannot steal connections
    from the HTTP budget even during a burst.
    """
    global _background_engine

    if _background_engine is not None:
        return _background_engine

    with _background_engine_lock:
        if _background_engine is not None:
            return _background_engine

        config = db_config or settings.database_data

        _background_engine = create_engine(
            _build_connection_url(config),
            poolclass=QueuePool,
            pool_size=4,
            max_overflow=0,        # fixed pool only — no overflow for background
            pool_recycle=3600,
            pool_pre_ping=True,
            pool_timeout=60,       # longer wait is acceptable for batch work
            echo=False,
            connect_args={
                "connect_timeout": 10,
                "read_timeout":    300,    # long timeout for batch operations
                "write_timeout":   300,
                "init_command":    "SET time_zone = '+00:00'",
            },
        )

        logger.info(
            "event=background_engine_created "
            "pool_size=4 max_overflow=0 pool_recycle=3600"
        )
        return _background_engine


def get_http_engine() -> Engine:
    """Return (or create) the shared HTTP engine."""
    return create_http_engine()


def get_background_engine() -> Engine:
    """Return (or create) the shared background engine."""
    return create_background_engine()


def dispose_engines() -> None:
    """
    Dispose all engine pools gracefully.

    Thread-safe: acquires each lock individually so HTTP and background
    disposal do not block each other.  Call during application shutdown.
    """
    global _http_engine, _background_engine

    with _http_engine_lock:
        if _http_engine is not None:
            _http_engine.dispose()
            _http_engine = None
            logger.info("event=http_engine_disposed")

    with _background_engine_lock:
        if _background_engine is not None:
            _background_engine.dispose()
            _background_engine = None
            logger.info("event=background_engine_disposed")


@contextmanager
def get_connection(
    engine: Engine | None = None,
    *,
    readonly: bool = False,
) -> Generator[Any, None, None]:
    """
    Context manager that borrows a connection from the pool.

    Fix: the original implementation always called conn.commit(), which is
    harmless but wasteful for SELECT-only queries.  Pass readonly=True to
    skip the commit entirely.

    Args:
        engine:   Engine to borrow from; defaults to the HTTP engine.
        readonly: When True the context manager skips commit() on exit.
                  Use this for pure SELECT queries to avoid unnecessary
                  round-trips to the server.

    Usage:
        # Read-only — no commit issued
        with get_connection(readonly=True) as conn:
            rows = conn.execute(text("SELECT * FROM tasks")).fetchall()

        # Read-write — commit on success, rollback on error
        with get_connection() as conn:
            conn.execute(text("UPDATE tasks SET status = :s"), {"s": "done"})
    """
    eng  = engine or get_http_engine()
    conn = eng.connect()
    try:
        yield conn
        if not readonly:
            conn.commit()
        # readonly path: no commit and no rollback — nothing was written
    except SQLAlchemyError as e:
        if not readonly:
            conn.rollback()
        logger.error("event=db_error error=%s", e)
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        conn.close()    # returns the connection to the pool


@contextmanager
def get_raw_connection(engine: Engine | None = None) -> Generator[Any, None, None]:
    """
    Return a raw DBAPI connection for code that cannot use SQLAlchemy text().

    Intended for backward-compatibility during migration only.
    Prefer get_connection() for new code.
    """
    eng  = engine or get_http_engine()
    conn = eng.raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

---

### 4.2 Flask Application Integration

`src/main_app/__init__.py`

```python
"""
Flask application factory with thread-safe connection pool initialization.

Fix: before_first_request was deprecated in Flask 2.3 and removed in Flask 3.0.
Use app.app_context() at startup for eager initialization instead.
"""

import atexit
from flask import Flask

from .db.engine_factory import get_http_engine, dispose_engines


def create_app() -> Flask:
    """Application factory — initializes the connection pool at startup."""
    app = Flask(__name__)

    # Initialize the engine once at startup (not lazily on first request).
    # This surfaces configuration errors immediately rather than on the
    # first production request.
    with app.app_context():
        get_http_engine()

    @app.teardown_appcontext
    def close_db(error: Exception | None) -> None:
        # Connections are returned to the pool automatically by the context
        # manager in get_connection(); nothing extra is needed here.
        pass

    @app.cli.command("db-pool-status")
    def pool_status() -> None:
        """Print current connection pool metrics to stdout."""
        engine      = get_http_engine()
        pool        = engine.pool
        total_cap   = pool.size() + pool.overflow()
        utilization = (pool.checkedout() / total_cap * 100) if total_cap > 0 else 0.0

        print(f"Pool size:    {pool.size()}")
        print(f"Checked in:   {pool.checkedin()}")
        print(f"Checked out:  {pool.checkedout()}")
        print(f"Overflow:     {pool.overflow()}")
        print(f"Utilization:  {utilization:.1f}%")
        print(
            f"Health:       "
            f"{'WARNING — consider scaling' if utilization > 80 else 'OK'}"
        )

    # Dispose engines cleanly when the process exits
    atexit.register(dispose_engines)

    return app
```

---

### 4.3 Compatibility Wrapper

`src/main_app/db/db_sqlalchemy.py`

```python
"""
Drop-in SQLAlchemy replacement for the legacy Database class.

Key improvements over v1.0:
  - readonly=True passed automatically for SELECT queries (no wasted commit)
  - Error 1203 retried with exponential backoff instead of raised immediately
  - _convert_placeholders uses a pre-compiled regex (minor performance fix)
"""

from __future__ import annotations

import logging
import random
import re
import time
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..config import DbConfig
from .engine_factory import DatabaseError, get_connection, get_http_engine

logger = logging.getLogger(__name__)

# Pre-compiled once at import time — avoids re-compiling per query call
_PLACEHOLDER_RE = re.compile(r"%s")


class MaxUserConnectionsError(DatabaseError):
    """Raised when MySQL error 1203 persists after all retry attempts."""
    pass


class DatabaseSQLAlchemy:
    """
    SQLAlchemy-based database wrapper compatible with the legacy Database interface.

    Replaces raw PyMySQL connections with pool-managed SQLAlchemy connections.
    All public methods mirror the original Database class API so callers
    require no changes.
    """

    # MySQL error codes that indicate a lost/reset connection and warrant a retry
    RETRYABLE_ERROR_CODES = {2006, 2013, 2014, 2017, 2018, 2055}

    # Retry settings for ordinary retryable connection errors
    MAX_RETRIES  = 3
    BASE_BACKOFF = 0.2   # seconds

    # Retry settings specifically for error 1203 (max_user_connections exceeded).
    # Fix: the original code raised 1203 immediately.  In practice the pool
    # releases a connection within a few seconds, so retrying is almost always
    # successful and far cheaper than surfacing the error to the user.
    ERROR_1203_MAX_RETRIES  = 3
    ERROR_1203_BASE_BACKOFF = 1.0   # longer base — connections free up slowly

    def __init__(
        self,
        database_data: DbConfig,
        use_background_engine: bool = False,
    ):
        self.db_config             = database_data
        self.use_background_engine = use_background_engine
        self._engine               = None

    @property
    def engine(self):
        """Lazy-load the appropriate engine on first access."""
        if self._engine is None:
            if self.use_background_engine:
                from .engine_factory import get_background_engine
                self._engine = get_background_engine()
            else:
                self._engine = get_http_engine()
        return self._engine

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _exception_code(self, exc: BaseException) -> int | None:
        """Extract the MySQL integer error code from a SQLAlchemy exception."""
        if hasattr(exc, "orig") and exc.orig:
            orig = exc.orig
            if hasattr(orig, "args") and orig.args:
                try:
                    return int(orig.args[0])
                except (IndexError, TypeError, ValueError):
                    pass
        return None

    def _compute_backoff(self, attempt: int, base: float = 0.2) -> float:
        """
        Exponential backoff with jitter.

        Formula: base * 2^(attempt-1) + uniform(0, 0.1)
        Jitter prevents a thundering-herd of retries hitting the DB at once.
        """
        return base * (2 ** (attempt - 1)) + random.uniform(0, 0.1)

    def _normalize_params(
        self, sql: str, params: Any
    ) -> tuple[str, dict | None]:
        """
        Convert PyMySQL-style positional %s placeholders to SQLAlchemy named params.

        Example:
            Input:  "SELECT * FROM t WHERE id = %s AND name = %s", [1, "bob"]
            Output: "SELECT * FROM t WHERE id = :p0 AND name = :p1",
                    {"p0": 1, "p1": "bob"}

        If params is already a dict (SQLAlchemy-native), it passes through unchanged.
        """
        if params is None:
            return sql, None

        if isinstance(params, dict):
            return sql, params   # already named — nothing to convert

        if isinstance(params, (list, tuple)):
            counter = iter(range(len(params)))
            converted = _PLACEHOLDER_RE.sub(
                lambda _: f":p{next(counter)}", sql
            )
            return converted, {f"p{i}": v for i, v in enumerate(params)}

        return sql, params

    # ── Core execution layer ──────────────────────────────────────────────────

    def _execute_with_retry(
        self,
        operation,
        sql_query: str,
        params: Any = None,
        readonly: bool = False,
    ):
        """
        Execute `operation(conn, sql, params)` with retry logic.

        Retry strategy:
          - Error 1203 (max_user_connections): retry up to ERROR_1203_MAX_RETRIES
            times with a longer backoff.  The pool usually frees a connection
            within seconds; waiting is cheaper than surfacing an error to users.
          - Connection-lost errors (RETRYABLE_ERROR_CODES): retry with a short
            exponential backoff — the server likely restarted or timed out.
          - All other errors: raise immediately, no retry.

        The `readonly` flag is forwarded to get_connection() so that SELECT
        queries never issue an unnecessary COMMIT round-trip.
        """
        last_exc: BaseException | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                with get_connection(self.engine, readonly=readonly) as conn:
                    return operation(conn, sql_query, params)

            except Exception as exc:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                code       = self._exception_code(exc)

                # ── Error 1203: wait for a pool slot to become free ──────────
                if code == 1203:
                    if attempt <= self.ERROR_1203_MAX_RETRIES:
                        wait = self._compute_backoff(
                            attempt, self.ERROR_1203_BASE_BACKOFF
                        )
                        logger.warning(
                            "event=max_user_connections_exceeded "
                            "attempt=%s/%s wait_s=%.2f — retrying",
                            attempt, self.ERROR_1203_MAX_RETRIES, wait,
                        )
                        time.sleep(wait)
                        last_exc = exc
                        continue
                    else:
                        logger.error(
                            "event=max_user_connections_exhausted attempts=%s",
                            attempt,
                        )
                        raise MaxUserConnectionsError(
                            f"MySQL max_user_connections exceeded after "
                            f"{attempt} retries"
                        ) from exc

                # ── Retryable connection errors ──────────────────────────────
                if (
                    code in self.RETRYABLE_ERROR_CODES
                    and attempt < self.MAX_RETRIES
                ):
                    wait = self._compute_backoff(attempt)
                    logger.debug(
                        "event=db_retry attempt=%s code=%s "
                        "elapsed_ms=%s wait_s=%.2f",
                        attempt, code, elapsed_ms, wait,
                    )
                    time.sleep(wait)
                    last_exc = exc
                    continue

                # ── Non-retryable error — raise immediately ──────────────────
                logger.error(
                    "event=db_error attempt=%s code=%s elapsed_ms=%s error=%s",
                    attempt, code, elapsed_ms, exc,
                )
                raise

        assert last_exc is not None
        raise last_exc

    # ── Public API (mirrors legacy Database class) ────────────────────────────

    def execute_query(self, sql_query: str, params: Any = None) -> list[dict] | int:
        """
        Execute any SQL statement.

        Returns a list of row dicts for SELECT, or rowcount (int) for DML.
        Automatically uses readonly=True for SELECT to skip the commit round-trip.
        """
        is_select = sql_query.strip().upper().startswith("SELECT")

        def _op(conn, sql, raw_params):
            converted_sql, named_params = self._normalize_params(sql, raw_params)
            result = conn.execute(text(converted_sql), named_params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            return result.rowcount

        return self._execute_with_retry(
            _op, sql_query, params, readonly=is_select
        )

    def fetch_query(
        self, sql_query: str, params: Any = None
    ) -> list[dict[str, Any]]:
        """
        Execute a SELECT query and return all matching rows.

        Always uses readonly=True — no commit is needed for reads.
        """
        def _op(conn, sql, raw_params):
            converted_sql, named_params = self._normalize_params(sql, raw_params)
            result = conn.execute(text(converted_sql), named_params or {})
            return [dict(row._mapping) for row in result]

        return self._execute_with_retry(_op, sql_query, params, readonly=True)

    def execute_many(
        self,
        sql_query: str,
        params_seq: Iterable[Any],
        batch_size: int = 1000,
    ) -> int:
        """
        Execute a DML statement for each row in params_seq.

        Rows are grouped into batches of `batch_size` and executed within a
        single connection borrow per batch, reducing pool churn.
        """
        params_list = list(params_seq)
        if not params_list:
            return 0

        def _op(conn, sql, _params_list):
            total = 0
            for i in range(0, len(_params_list), batch_size):
                batch = _params_list[i : i + batch_size]
                if batch and isinstance(batch[0], (list, tuple)):
                    # Convert positional placeholders for each batch row
                    row_len = len(batch[0])
                    c = iter(range(row_len))
                    converted = _PLACEHOLDER_RE.sub(lambda _: f":p{next(c)}", sql)
                    named_batch = [
                        {f"p{j}": v for j, v in enumerate(row)} for row in batch
                    ]
                else:
                    converted   = sql
                    named_batch = batch

                result = conn.execute(text(converted), named_batch)
                total += result.rowcount
            return total

        return self._execute_with_retry(_op, sql_query, params_list)

    def fetch_query_safe(
        self, sql_query: str, params: Any = None
    ) -> list[dict]:
        """Execute a SELECT; return [] on any error instead of raising."""
        try:
            return self.fetch_query(sql_query, params)
        except SQLAlchemyError as e:
            logger.error(
                "event=db_fetch_safe_failed sql=%s error=%s", sql_query, e
            )
            return []

    def execute_query_safe(
        self, sql_query: str, params: Any = None
    ) -> list | int:
        """Execute a statement; return [] or 0 on any error instead of raising."""
        try:
            return self.execute_query(sql_query, params)
        except SQLAlchemyError as e:
            logger.error(
                "event=db_execute_safe_failed sql=%s error=%s", sql_query, e
            )
            return [] if sql_query.strip().upper().startswith("SELECT") else 0

    def close(self) -> None:
        """No-op — connection lifecycle is managed by the pool."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.close()
```

---

## 5. Batch Processing Patterns

`src/main_app/db/batch_processor.py`

```python
"""
Batch processing patterns with connection pooling for background workers.

Designed for the 700-file processing workload while staying within the
Toolforge connection budget.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable, TypeVar

from sqlalchemy import text

from .engine_factory import get_background_engine, get_connection

logger = logging.getLogger(__name__)
T = TypeVar("T")
R = TypeVar("R")


class BatchProcessor:
    """
    Process large batches of items with controlled concurrency.

    max_workers should not exceed the background engine's pool_size (4).
    Each worker borrows exactly one connection at a time, so:
      peak connections = max_workers x pods = 4 x 2 = 8
    """

    def __init__(self, max_workers: int = 4, batch_size: int = 50):
        # Warn if caller requests more workers than pool slots available
        if max_workers > 4:
            logger.warning(
                "event=batch_worker_count_warning "
                "max_workers=%s bg_pool_size=4 — "
                "excess workers will queue on the pool and slow throughput",
                max_workers,
            )
        self.max_workers = max_workers
        self.batch_size  = batch_size
        self.engine      = get_background_engine()

    def process_items(
        self,
        items: Iterable[T],
        processor: Callable[[T, Any], R],
        error_handler: Callable[[T, Exception], None] | None = None,
    ) -> list[R]:
        """
        Process items concurrently using a thread pool backed by the connection pool.

        Each worker borrows one connection, processes one item, then returns the
        connection to the pool before picking up the next item.

        Args:
            items:         Items to process.
            processor:     Function(item, db_conn) -> result called per item.
            error_handler: Optional callback(item, exc) on per-item failures.

        Returns:
            List of successful results (failed items are excluded).
        """
        items_list     = list(items)
        results, errors = [], []

        logger.info(
            "event=batch_start items=%s workers=%s batch_size=%s",
            len(items_list), self.max_workers, self.batch_size,
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {
                executor.submit(self._process_single, item, processor): item
                for item in items_list
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    logger.error(
                        "event=batch_item_error item=%s error=%s", item, exc
                    )
                    errors.append((item, exc))
                    if error_handler:
                        error_handler(item, exc)

        logger.info(
            "event=batch_complete total=%s success=%s errors=%s",
            len(items_list), len(results), len(errors),
        )
        return results

    def _process_single(self, item: T, processor: Callable[[T, Any], R]) -> R:
        """Borrow one connection from the pool, process the item, return connection."""
        with get_connection(self.engine) as conn:
            return processor(item, conn)

    def bulk_insert(
        self,
        table: str,
        records: list[dict],
        on_duplicate: str | None = None,
    ) -> int:
        """
        Insert records in batches of self.batch_size.

        Args:
            table:        Target table name.
            records:      List of row dicts; all must share the same keys.
            on_duplicate: Optional ON DUPLICATE KEY UPDATE clause.

        Returns:
            Total rows affected.
        """
        if not records:
            return 0

        total   = 0
        columns = list(records[0].keys())

        # Build INSERT template once, outside the batch loop
        placeholders = ", ".join(f":{col}" for col in columns)
        columns_str  = ", ".join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        if on_duplicate:
            sql += f" {on_duplicate}"

        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            with get_connection(self.engine) as conn:
                result = conn.execute(text(sql), batch)
                total += result.rowcount

            logger.debug(
                "event=bulk_insert_batch batch=%s/%s rows=%s",
                i // self.batch_size + 1,
                -(-len(records) // self.batch_size),   # ceiling division
                result.rowcount,
            )

        return total

    def chunked_query(
        self,
        sql: str,
        params: dict | None = None,
        chunk_size: int = 1000,
    ):
        """
        Yield query results in chunks to limit memory usage.

        Each chunk borrows and immediately returns one connection, keeping the
        pool free between chunks for other workers.

        Usage:
            for chunk in processor.chunked_query("SELECT * FROM tasks"):
                process(chunk)
        """
        offset = 0
        while True:
            chunk_sql = f"{sql} LIMIT {chunk_size} OFFSET {offset}"
            with get_connection(self.engine, readonly=True) as conn:
                result = conn.execute(text(chunk_sql), params or {})
                rows   = [dict(row._mapping) for row in result]

            if not rows:
                break

            yield rows
            offset += chunk_size

            # Stop early if the last page was partial (no more rows remain)
            if len(rows) < chunk_size:
                break
```

---

## 6. Monitoring and Observability

`src/main_app/db/pool_monitor.py`

```python
"""Connection pool monitoring — periodic metrics logging and health checks."""

from __future__ import annotations

import logging
import time

from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Alert threshold: emit a WARNING when utilisation exceeds this value
HIGH_UTILIZATION_THRESHOLD = 0.80   # 80%


class PoolMonitor:
    """Periodically sample and log connection pool metrics."""

    def __init__(self, engine: Engine, name: str, log_interval: int = 60):
        self.engine       = engine
        self.name         = name
        self.log_interval = log_interval   # seconds between automatic log calls
        self._last_log_ts = 0.0

    def log_status(self, force: bool = False) -> None:
        """
        Log current pool metrics.

        Respects log_interval to avoid flooding the log; pass force=True
        to emit immediately regardless of the interval.
        """
        now = time.time()
        if not force and (now - self._last_log_ts) < self.log_interval:
            return

        self._last_log_ts = now
        pool      = self.engine.pool
        total_cap = pool.size() + max(pool.overflow(), 0)
        util      = pool.checkedout() / total_cap if total_cap > 0 else 0.0

        level = logging.WARNING if util > HIGH_UTILIZATION_THRESHOLD else logging.INFO

        logger.log(
            level,
            "event=pool_status name=%s size=%s checked_in=%s "
            "checked_out=%s overflow=%s utilization=%.1f%%",
            self.name, pool.size(), pool.checkedin(),
            pool.checkedout(), pool.overflow(), util * 100,
        )

    def metrics_dict(self) -> dict:
        """Return current pool metrics as a plain dict (for health endpoints)."""
        pool = self.engine.pool
        return {
            "pool_size":   pool.size(),
            "checked_in":  pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow":    pool.overflow(),
            "utilization": round(pool.checkedout() / (pool.size() or 1) * 100, 1),
        }
```

### 6.1 Health Check Endpoint

```python
# src/main_app/routes/health.py
from flask import jsonify
from sqlalchemy import text

from ..db.engine_factory import get_http_engine
from ..db.pool_monitor   import PoolMonitor


@app.route("/health/db")
def db_health_check():
    """Return pool statistics and a liveness result for the database."""
    engine  = get_http_engine()
    monitor = PoolMonitor(engine, "http")

    try:
        # Lightweight liveness probe — borrows and returns one connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()

        return jsonify({
            "status": "healthy",
            "pool":   monitor.metrics_dict(),
        }), 200

    except Exception as exc:
        logger.error("event=health_check_failed error=%s", exc)
        return jsonify({
            "status": "unhealthy",
            "error":  str(exc),
        }), 503
```

---

## 7. Migration Steps

### 7.1 Phase 1 — Add Dependencies

`requirements.txt`:

```txt
sqlalchemy>=2.0.0
pymysql>=1.1.0      # already present — verify version compatibility
```

### 7.2 Phase 2 — Create Engine Factory (Parallel)

1. Create `src/main_app/db/engine_factory.py` (Section 4.1)
2. Create `src/main_app/db/db_sqlalchemy.py` (Section 4.3)
3. Create `src/main_app/db/pool_monitor.py` (Section 6)
4. Run unit tests to verify backward compatibility

### 7.3 Phase 3 — Gradual Migration with Feature Flag

`src/main_app/db/task_store_pymysql.py`:

```python
import os
from .db_sqlalchemy import DatabaseSQLAlchemy

# Feature flag — allows instant rollback via environment variable without redeploy
_USE_POOLING = os.getenv("USE_SQLALCHEMY_POOLING", "true").lower() == "true"


class TaskStorePyMysql(CreateUpdateTask, StageStore, TasksListDB, DbUtils):
    """MySQL-backed task store with optional SQLAlchemy connection pooling."""

    def __init__(
        self, database_data: DbConfig, use_pooling: bool = _USE_POOLING
    ):
        if use_pooling:
            self.db = DatabaseSQLAlchemy(database_data)
        else:
            # Fallback to legacy PyMySQL for gradual migration / emergency rollback
            from .db_class import Database
            self.db = Database(database_data)

        self._init_schema()
        super().__init__(self.db)
```

### 7.4 Phase 4 — Background Worker Migration

```python
# In each worker file under jobs_workers/
from ..db.engine_factory import get_background_engine

class SomeWorker:
    def __init__(self):
        # Shared pool — not a new connection per worker instance
        self.engine = get_background_engine()
```

### 7.5 Phase 5 — Remove Legacy Code

Once all components are stable in production:

1. Delete `src/main_app/db/db_class.py`
2. Rename `TaskStorePyMysql` → `TaskStore`
3. Remove the `use_pooling` parameter and `_USE_POOLING` env check
4. Update all imports accordingly

### 7.6 Migration Checklist

-   [ ] Add SQLAlchemy to `requirements.txt`
-   [ ] Create `engine_factory.py`
-   [ ] Create `db_sqlalchemy.py`
-   [ ] Create `pool_monitor.py`
-   [ ] Update `TaskStore` with feature flag
-   [ ] Migrate HTTP routes (test each route individually)
-   [ ] Migrate background workers
-   [ ] Update batch processing code
-   [ ] Add `/health/db` endpoint
-   [ ] Load test in staging (verify peak connections ≤ 88)
-   [ ] Deploy to production with `USE_SQLALCHEMY_POOLING=true`
-   [ ] Monitor pool metrics for 48 hours
-   [ ] Remove legacy code after stability confirmed

---

## 8. Risk Analysis

| Risk                              | Likelihood | Impact   | Mitigation                                                                                               |
| --------------------------------- | ---------- | -------- | -------------------------------------------------------------------------------------------------------- |
| **SQL Syntax Incompatibility**    | Medium     | High     | `_normalize_params()` converts `%s` to `:pN` automatically; complex queries may still need manual review |
| **Transaction Behaviour Changes** | Medium     | High     | SQLAlchemy defaults to `autocommit=False`; test all write paths explicitly                               |
| **Pool Exhaustion Under Load**    | Low        | High     | Monitor utilisation; alert at 80%; scale `pool_size` if sustained high usage                             |
| **Connection Leaks**              | Low        | Critical | Always use `with get_connection()`; `pool_pre_ping=True` detects stale connections                       |
| **Performance Regression**        | Low        | Medium   | Pooling overhead is negligible vs connection setup cost; benchmark before/after                          |
| **Background Worker Starvation**  | Low        | High     | Separate engine with `max_overflow=0` guarantees HTTP pool is never exhausted                            |
| **Migration Rollback**            | Low        | High     | `USE_SQLALCHEMY_POOLING=false` reverts to legacy code instantly without redeployment                     |

---

## 9. Production Hardening Checklist

### Pre-Deployment

-   [ ] Load test with 2× expected traffic
-   [ ] Verify peak connection count stays under 88 (`SHOW STATUS LIKE 'Threads_connected'`)
-   [ ] Test error 1203 scenario (temporarily set `max_user_connections=10`)
-   [ ] Verify retry logic recovers from 1203 without surfacing error to end-users
-   [ ] Test background worker isolation (HTTP requests unaffected during batch run)

### Configuration

-   [ ] `pool_recycle` < MySQL `wait_timeout` (server default: 28800 s)
-   [ ] `pool_pre_ping = True` enabled on all engines
-   [ ] `pool_timeout` set (HTTP: 30 s, background: 60 s)
-   [ ] Separate engines confirmed for HTTP and background work
-   [ ] `echo = False` in production

### Monitoring

-   [ ] Pool metrics logged every 60 s via `PoolMonitor`
-   [ ] Alert when utilisation exceeds 80%
-   [ ] Alert when connection wait time exceeds 1 s
-   [ ] MySQL `Threads_connected` tracked via `SHOW STATUS`
-   [ ] `/health/db` endpoint integrated with uptime monitoring tool

### Security

-   [ ] Credentials stored in environment variables only — never in source code
-   [ ] `URL.create()` used everywhere — no plaintext f-string connection URLs
-   [ ] `echo = False` confirmed (no SQL statements in production logs)
-   [ ] SSL/TLS configured if Toolforge supports it
-   [ ] SQL injection review: all user input uses parameterised queries

---

## Appendix A: Quick Reference

### Common Issues and Solutions

| Symptom                                     | Cause                              | Solution                                         |
| ------------------------------------------- | ---------------------------------- | ------------------------------------------------ |
| Error 1203 persists after retries           | Pool too large for MySQL budget    | Reduce values using the formula in §3.2          |
| Slow HTTP responses during batch            | Background pool starving HTTP pool | Verify separate engines are in use               |
| Stale connection errors                     | MySQL `wait_timeout` elapsed       | Enable `pool_pre_ping`; reduce `pool_recycle`    |
| Memory growth over time                     | Connections not returned to pool   | Check for missing `with get_connection()` blocks |
| Auth failure with special chars in password | f-string URL encoding bug          | Confirm `URL.create()` is used (§4.1)            |
| Race condition on startup                   | No lock on engine initialization   | Confirm `threading.Lock` is in place (§4.1)      |

### Connection String Reference

```python
# Standard Toolforge — always use URL.create(), never an f-string
from sqlalchemy.engine import URL

url = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],   # special characters encoded automatically
    host=os.environ["DB_HOST"],
    database=os.environ["DB_NAME"],
    query={"charset": "utf8mb4"},
)

# With SSL
url = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    database=os.environ["DB_NAME"],
    query={
        "charset": "utf8mb4",
        "ssl_ca":  "/etc/ssl/certs/ca-certificates.crt",
    },
)
```

---

## Document Information

| Field            | Value                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------- |
| **Version**      | 2.0 (Improved)                                                                           |
| **Based on**     | v1.0 — 2026-02-26                                                                        |
| **Key changes**  | Connection budget fix · `URL.create()` · `threading.Lock` · `readonly` mode · 1203 retry |
| **Review Cycle** | Quarterly                                                                                |
