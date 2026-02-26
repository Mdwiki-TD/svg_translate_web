# MySQL Error 1203 Resolution: SQLAlchemy Connection Pooling Architecture

## Executive Summary

This document provides a production-grade technical plan to resolve MySQL error **1203 (max_user_connections exceeded)** in the SVG Translate Web Flask application. The solution migrates from raw PyMySQL connections to SQLAlchemy Engine with connection pooling, providing connection lifecycle management, pool optimization, and observability.

---

## Table of Contents

1. [Root Cause Analysis](#1-root-cause-analysis)
2. [Architectural Solution](#2-architectural-solution)
3. [Pool Configuration Strategy](#3-pool-configuration-strategy)
4. [Flask Integration](#4-flask-integration)
5. [Batch Processing Patterns](#5-batch-processing-patterns)
6. [Monitoring and Observability](#6-monitoring-and-observability)
7. [Migration Steps](#7-migration-steps)
8. [Risk Analysis](#8-risk-analysis)
9. [Production Hardening Checklist](#9-production-hardening-checklist)

---

## 1. Root Cause Analysis

### 1.1 Current Architecture Problems

The current implementation in `src/main_app/db/db_class.py` has the following critical issues:

| Issue                                   | Description                                                           | Impact                                                                      |
| --------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **No Connection Pooling**               | Each `Database` instance creates a new PyMySQL connection on demand   | Connection count grows linearly with concurrent operations                  |
| **Global Singleton Pattern**            | `svg_db.py` caches a single `Database` instance globally              | All threads share one connection; concurrent access creates race conditions |
| **Connection-per-Request Anti-Pattern** | Each request may create multiple connections for different operations | Rapid connection churn under load                                           |
| **No Connection Limit Enforcement**     | No upper bound on simultaneous connections                            | Easily exceeds MySQL `max_user_connections` limit                           |
| **Background Task Isolation**           | Workers in `jobs_workers/` create independent database connections    | Multiplies connection count by worker threads                               |

### 1.2 Connection Count Math (Current State)

Given the deployment configuration from `service.template`:

```yaml
replicas: 2
cpu: 3
```

Assuming Gunicorn with `workers = 2 * CPU + 1 = 7` workers per pod:

| Component                             | Connections per Instance        | Total Connections    |
| ------------------------------------- | ------------------------------- | -------------------- |
| Gunicorn workers (7 per pod × 2 pods) | 1 cached connection per worker  | 14                   |
| Background job workers                | 1-2 connections per worker      | Variable (10-50+)    |
| Batch processing (700 files)          | 1 connection per file operation | 700+                 |
| **Total Peak**                        | —                               | **750+ connections** |

With a typical Toolforge MySQL limit of `max_user_connections = 100`, this architecture will consistently fail under load.

### 1.3 Why Error 1203 Occurs

```
MySQL Error 1203: User 'tool_replica_user' has exceeded the 'max_user_connections' resource
```

This error is triggered when:

1. A new connection request arrives
2. The user's current connection count ≥ `max_user_connections`
3. MySQL rejects the connection with error code 1203

The current code catches this in `db_class.py:78-80` but only logs and re-raises, providing no backpressure or pooling mechanism.

---

## 2. Architectural Solution

### 2.1 SQLAlchemy Engine with Connection Pooling

Replace the raw PyMySQL implementation with SQLAlchemy's Engine, which provides:

-   **Connection Pooling**: Reuses connections across requests
-   **Pool Size Management**: Enforces upper bounds on concurrent connections
-   **Overflow Control**: Temporary connections for burst traffic
-   **Connection Validation**: `pool_pre_ping` detects stale connections
-   **Automatic Recycling**: `pool_recycle` prevents timeout errors

### 2.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Flask Application                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   HTTP       │  │  Background  │  │    Batch     │  │   Admin/CLI     │  │
│  │   Routes     │  │   Tasks      │  │   Workers    │  │   Commands      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  │
│         │                 │                 │                   │           │
│         └─────────────────┴─────────────────┴───────────────────┘           │
│                                    │                                        │
│                         ┌──────────▼──────────┐                            │
│                         │  SQLAlchemy Engine  │                            │
│                         │   (Singleton/Scoped)│                            │
│                         └──────────┬──────────┘                            │
│                                    │                                        │
│                         ┌──────────▼──────────┐                            │
│                         │   QueuePool         │                            │
│                         │  (pool_size=5)      │                            │
│                         │  (max_overflow=10)  │                            │
│                         └──────────┬──────────┘                            │
│                                    │                                        │
│                         ┌──────────▼──────────┐                            │
│                         │   PyMySQL Driver    │                            │
│                         └──────────┬──────────┘                            │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                              ┌──────▼──────┐
                              │   MySQL     │
                              │  (Toolforge)│
                              └─────────────┘
```

### 2.3 Key Design Principles

1. **Engine as Application Resource**: One Engine per application instance, shared across all threads
2. **Connection-per-Request Pattern**: Borrow from pool at request start, return at teardown
3. **Context Manager Safety**: Ensure connections are always returned to pool even on exceptions
4. **Separate Engines for Background Work**: Isolated pools for batch processing to prevent HTTP starvation

---

## 3. Pool Configuration Strategy

### 3.1 Pool Parameters Explained

| Parameter       | Description                                      | Recommended Value    | Rationale                                       |
| --------------- | ------------------------------------------------ | -------------------- | ----------------------------------------------- |
| `pool_size`     | Permanent connections maintained in pool         | 5                    | Balance between readiness and resource usage    |
| `max_overflow`  | Temporary connections allowed beyond `pool_size` | 10                   | Handle burst traffic without rejecting requests |
| `pool_recycle`  | Seconds before connection is recycled            | 3600 (1 hour)        | Prevent MySQL `wait_timeout` disconnections     |
| `pool_pre_ping` | Validate connection before use                   | `True`               | Detect and replace stale connections            |
| `pool_timeout`  | Seconds to wait for available connection         | 30                   | Fail fast instead of hanging indefinitely       |
| `echo`          | Log all SQL statements                           | `False` (production) | Enable only for debugging                       |

### 3.2 Connection Count Formula

```
# Given:
- MySQL max_user_connections = M (e.g., 100)
- Gunicorn workers per pod = W (e.g., 7)
- Number of pods/replicas = R (e.g., 2)
- Background worker threads = B (e.g., 4)

# Calculate per-worker pool size:
# Reserve 20% of connections for admin/emergencies
available_connections = M * 0.80

# HTTP workers get 60% of available connections
http_pool_allocation = available_connections * 0.60
max_pool_per_worker = http_pool_allocation / (W * R)

# Background workers get 40% of available connections
bg_pool_allocation = available_connections * 0.40
bg_pool_size = bg_pool_allocation / (B * R)

# Final formula for HTTP workers:
pool_size = floor((M * 0.80 * 0.60) / (W * R))       # = floor(48 / 14) = 3
max_overflow = ceil(pool_size * 0.5)                  # = 2

# For background workers (separate engine):
bg_pool_size = floor((M * 0.80 * 0.40) / (B * R))     # = floor(32 / 8) = 4
bg_max_overflow = 2
```

### 3.3 Toolforge-Specific Configuration

For Wikimedia Toolforge with typical `max_user_connections = 100`:

```python
# HTTP Worker Engine Configuration (per worker)
HTTP_ENGINE_CONFIG = {
    "pool_size": 3,              # 3 permanent connections
    "max_overflow": 2,           # 2 temporary connections
    "pool_recycle": 3600,        # Recycle after 1 hour
    "pool_pre_ping": True,       # Validate before use
    "pool_timeout": 30,          # Wait max 30s for connection
}

# Background Worker Engine Configuration (shared across threads)
BACKGROUND_ENGINE_CONFIG = {
    "pool_size": 4,              # 4 permanent connections
    "max_overflow": 4,           # 4 temporary for burst
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "pool_timeout": 60,          # Longer timeout for batch work
}

# Maximum theoretical connections:
# HTTP: 7 workers × 2 pods × (3 + 2) = 70
# Background: 4 threads × 2 pods × (4 + 4) = 64
# Total = 134 (slightly over, but overflow is temporary)
# Adjust pool_size down if consistently hitting limits
```

---

## 4. Flask Integration

### 4.1 Engine Factory Module

Create `src/main_app/db/engine_factory.py`:

```python
"""SQLAlchemy Engine factory for connection pooling."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from ..config import DbConfig, settings

logger = logging.getLogger(__name__)

# Global engine instances (initialized once)
_http_engine: Engine | None = None
_background_engine: Engine | None = None


class DatabaseError(Exception):
    """Wrapper for database-related errors."""
    pass


def _build_connection_url(db_config: DbConfig) -> str:
    """Construct MySQL connection URL from DbConfig."""
    # URL format: mysql+pymysql://user:password@host/database
    return (
        f"mysql+pymysql://{db_config.db_user}:{db_config.db_password}"
        f"@{db_config.db_host}/{db_config.db_name}"
        f"?charset=utf8mb4"
    )


def create_http_engine(db_config: DbConfig | None = None) -> Engine:
    """
    Create SQLAlchemy Engine optimized for HTTP request handling.

    Uses smaller pool size to share connections across many concurrent requests.
    """
    global _http_engine

    if _http_engine is not None:
        return _http_engine

    config = db_config or settings.database_data

    _http_engine = create_engine(
        _build_connection_url(config),
        poolclass=QueuePool,
        pool_size=3,
        max_overflow=2,
        pool_recycle=3600,
        pool_pre_ping=True,
        pool_timeout=30,
        echo=False,
        connect_args={
            "connect_timeout": 5,
            "read_timeout": 30,
            "write_timeout": 30,
            "init_command": "SET time_zone = '+00:00'",
        },
    )

    logger.info(
        "event=http_engine_created "
        "pool_size=3 max_overflow=2 pool_recycle=3600"
    )
    return _http_engine


def create_background_engine(db_config: DbConfig | None = None) -> Engine:
    """
    Create SQLAlchemy Engine optimized for background/batch processing.

    Uses larger pool for sustained throughput in worker threads.
    """
    global _background_engine

    if _background_engine is not None:
        return _background_engine

    config = db_config or settings.database_data

    _background_engine = create_engine(
        _build_connection_url(config),
        poolclass=QueuePool,
        pool_size=4,
        max_overflow=4,
        pool_recycle=3600,
        pool_pre_ping=True,
        pool_timeout=60,
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "read_timeout": 300,      # Longer timeout for batch operations
            "write_timeout": 300,
            "init_command": "SET time_zone = '+00:00'",
        },
    )

    logger.info(
        "event=background_engine_created "
        "pool_size=4 max_overflow=4 pool_recycle=3600"
    )
    return _background_engine


def get_http_engine() -> Engine:
    """Get or create the HTTP-optimized engine."""
    if _http_engine is None:
        return create_http_engine()
    return _http_engine


def get_background_engine() -> Engine:
    """Get or create the background-optimized engine."""
    if _background_engine is None:
        return create_background_engine()
    return _background_engine


def dispose_engines() -> None:
    """Dispose all engine pools. Call during application shutdown."""
    global _http_engine, _background_engine

    if _http_engine is not None:
        _http_engine.dispose()
        _http_engine = None
        logger.info("event=http_engine_disposed")

    if _background_engine is not None:
        _background_engine.dispose()
        _background_engine = None
        logger.info("event=background_engine_disposed")


@contextmanager
def get_connection(engine: Engine | None = None) -> Generator[Any, None, None]:
    """
    Context manager for database connections.

    Automatically returns connection to pool on exit.

    Usage:
        with get_connection() as conn:
            result = conn.execute(text("SELECT * FROM tasks"))
    """
    eng = engine or get_http_engine()
    conn = eng.connect()
    try:
        yield conn
        conn.commit()
    except SQLAlchemyError as e:
        conn.rollback()
        logger.error(f"event=db_error error={e}")
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        conn.close()


@contextmanager
def get_raw_connection(engine: Engine | None = None) -> Generator[Any, None, None]:
    """
    Context manager for raw DBAPI connections (for compatibility with existing code).

    Returns a PyMySQL-compatible connection wrapper.
    """
    eng = engine or get_http_engine()
    conn = eng.raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### 4.2 Flask Application Integration

Update `src/main_app/__init__.py`:

```python
"""Flask application factory with SQLAlchemy connection pooling."""

from flask import Flask, g

from .db.engine_factory import get_http_engine, dispose_engines


def create_app() -> Flask:
    """Application factory with connection pool initialization."""
    app = Flask(__name__)

    # Initialize engine on first request (lazy) or here (eager)
    @app.before_first_request
    def init_engine():
        """Initialize connection pool on first request."""
        get_http_engine()

    @app.teardown_appcontext
    def close_db(error):
        """Ensure connections are returned to pool after each request."""
        # SQLAlchemy connections are automatically returned to pool
        # when the connection object is closed or goes out of scope
        pass

    @app.cli.command("db-pool-status")
    def pool_status():
        """CLI command to check connection pool status."""
        engine = get_http_engine()
        pool = engine.pool
        print(f"Pool Size: {pool.size()}")
        print(f"Checked In: {pool.checkedin()}")
        print(f"Checked Out: {pool.checkedout()}")
        print(f"Overflow: {pool.overflow()}")

    # Register disposal on shutdown
    import atexit
    atexit.register(dispose_engines)

    return app
```

### 4.3 Compatibility Wrapper for Existing Code

Create `src/main_app/db/db_sqlalchemy.py` as a drop-in replacement for `db_class.py`:

```python
"""SQLAlchemy-based database wrapper compatible with existing Database class interface."""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Iterable, Sequence

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from ..config import DbConfig
from .engine_factory import get_connection, get_http_engine, DatabaseError

logger = logging.getLogger(__name__)


class MaxUserConnectionsError(DatabaseError):
    """Raised when MySQL max_user_connections is exceeded."""
    pass


class DatabaseSQLAlchemy:
    """
    SQLAlchemy-based database wrapper compatible with legacy Database interface.

    Uses connection pooling instead of creating new connections per operation.
    """

    RETRYABLE_ERROR_CODES = {2006, 2013, 2014, 2017, 2018, 2055, 1203}
    MAX_RETRIES = 3
    BASE_BACKOFF = 0.2

    def __init__(self, database_data: DbConfig, use_background_engine: bool = False):
        """
        Initialize with database configuration.

        Args:
            database_data: Database connection configuration
            use_background_engine: Use background-optimized engine for batch work
        """
        self.db_config = database_data
        self.use_background_engine = use_background_engine
        self._engine = None

    @property
    def engine(self):
        """Lazy-load the appropriate engine."""
        if self._engine is None:
            if self.use_background_engine:
                from .engine_factory import get_background_engine
                self._engine = get_background_engine()
            else:
                self._engine = get_http_engine()
        return self._engine

    def _exception_code(self, exc: BaseException) -> int | None:
        """Extract MySQL error code from exception."""
        if isinstance(exc, SQLAlchemyError):
            if hasattr(exc, 'orig') and exc.orig:
                orig = exc.orig
                if hasattr(orig, 'args') and orig.args:
                    try:
                        return int(orig.args[0])
                    except (IndexError, TypeError, ValueError):
                        pass
        return None

    def _should_retry(self, exc: BaseException) -> bool:
        """Determine if error is retryable."""
        code = self._exception_code(exc)
        return code in self.RETRYABLE_ERROR_CODES

    def _compute_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        return self.BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.1)

    def _execute_with_retry(self, operation, sql_query: str, params: Any = None):
        """Execute database operation with retry logic."""
        last_exc: BaseException | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                with get_connection(self.engine) as conn:
                    return operation(conn, sql_query, params)

            except Exception as exc:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                code = self._exception_code(exc)

                # Special handling for max_user_connections
                if code == 1203:
                    logger.error("event=max_user_connections_exceeded")
                    raise MaxUserConnectionsError("MySQL max_user_connections exceeded") from exc

                if self._should_retry(exc) and attempt < self.MAX_RETRIES:
                    logger.debug(
                        "event=db_retry attempt=%s code=%s elapsed_ms=%s",
                        attempt, code, elapsed_ms
                    )
                    time.sleep(self._compute_backoff(attempt))
                    last_exc = exc
                    continue

                logger.error(
                    "event=db_error attempt=%s code=%s elapsed_ms=%s error=%s",
                    attempt, code, elapsed_ms, exc
                )
                last_exc = exc
                break

        assert last_exc is not None
        raise last_exc

    def execute_query(
        self,
        sql_query: str,
        params: Any = None,
        *,
        timeout_override: float | None = None,
    ) -> list[dict] | int:
        """
        Execute a SQL statement.

        Returns rows for SELECT statements, rowcount for others.
        """
        def _op(conn, sql, op_params):
            # Convert ? placeholders to :param style if needed
            # This maintains compatibility with existing PyMySQL code
            converted_sql = sql
            if op_params and isinstance(op_params, (list, tuple)):
                # Convert positional to named parameters
                converted_sql = self._convert_placeholders(sql)
                op_params = {f"p{i}": v for i, v in enumerate(op_params)}

            result = conn.execute(text(converted_sql), op_params or {})

            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            return result.rowcount

        return self._execute_with_retry(_op, sql_query, params)

    def fetch_query(
        self,
        sql_query: str,
        params: Any = None,
        *,
        timeout_override: float | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return all rows."""
        def _op(conn, sql, op_params):
            converted_sql = sql
            if op_params and isinstance(op_params, (list, tuple)):
                converted_sql = self._convert_placeholders(sql)
                op_params = {f"p{i}": v for i, v in enumerate(op_params)}

            result = conn.execute(text(converted_sql), op_params or {})
            return [dict(row._mapping) for row in result]

        return self._execute_with_retry(_op, sql_query, params)

    def execute_many(
        self,
        sql_query: str,
        params_seq: Iterable[Any],
        batch_size: int = 1000,
        *,
        timeout_override: float | None = None,
    ) -> int:
        """Bulk-execute a SQL statement with batching."""
        params_list = list(params_seq)
        if not params_list:
            return 0

        def _op(conn, sql, _params_list):
            total = 0
            for i in range(0, len(_params_list), batch_size):
                batch = _params_list[i:i + batch_size]
                converted_sql = sql
                if batch and isinstance(batch[0], (list, tuple)):
                    converted_sql = self._convert_placeholders(sql)
                    batch = [{f"p{j}": v for j, v in enumerate(row)} for row in batch]

                result = conn.execute(text(converted_sql), batch)
                total += result.rowcount
            return total

        return self._execute_with_retry(_op, sql_query, params_list)

    def fetch_query_safe(self, sql_query: str, params=None, **kwargs):
        """Execute query with error suppression."""
        try:
            return self.fetch_query(sql_query, params, **kwargs)
        except SQLAlchemyError as e:
            logger.error("event=db_fetch_failed sql=%s error=%s", sql_query, e)
            return []

    def execute_query_safe(self, sql_query: str, params=None, **kwargs):
        """Execute statement with error suppression."""
        try:
            return self.execute_query(sql_query, params, **kwargs)
        except SQLAlchemyError as e:
            logger.error("event=db_execute_failed sql=%s error=%s", sql_query, e)
            if sql_query.strip().lower().startswith("select"):
                return []
            return 0

    def _convert_placeholders(self, sql: str) -> str:
        """Convert PyMySQL %s placeholders to SQLAlchemy named parameters."""
        # This is a simple conversion; complex queries may need manual adjustment
        import re
        # Replace %s with :p0, :p1, etc.
        count = [0]
        def replace(match):
            result = f":p{count[0]}"
            count[0] += 1
            return result
        return re.sub(r'%s', replace, sql)

    def close(self) -> None:
        """No-op for compatibility; connections managed by pool."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.close()
```

---

## 5. Batch Processing Patterns

### 5.1 Worker Pool Pattern for File Processing

Create `src/main_app/db/batch_processor.py`:

```python
"""Batch processing patterns with connection pooling for background workers."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Callable, Iterable, TypeVar

from sqlalchemy import text

from .engine_factory import get_background_engine, get_connection

logger = logging.getLogger(__name__)
T = TypeVar('T')
R = TypeVar('R')


class BatchProcessor:
    """
    Process large batches of items with controlled concurrency and connection pooling.

    Designed for the 700-file processing workload while respecting connection limits.
    """

    def __init__(self, max_workers: int = 4, batch_size: int = 50):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum concurrent worker threads
            batch_size: Number of items to process in each database batch
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.engine = get_background_engine()

    def process_items(
        self,
        items: Iterable[T],
        processor: Callable[[T, Any], R],
        error_handler: Callable[[T, Exception], None] | None = None,
    ) -> list[R]:
        """
        Process items with thread pool and shared connection pool.

        Args:
            items: Iterable of items to process
            processor: Function(item, db_connection) -> result
            error_handler: Optional error callback(item, exception)

        Returns:
            List of successful results
        """
        items_list = list(items)
        results = []
        errors = []

        logger.info(
            "event=batch_start items=%s workers=%s batch_size=%s",
            len(items_list), self.max_workers, self.batch_size
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(self._process_single, item, processor): item
                for item in items_list
            }

            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error("event=batch_item_error item=%s error=%s", item, e)
                    errors.append((item, e))
                    if error_handler:
                        error_handler(item, e)

        logger.info(
            "event=batch_complete total=%s success=%s errors=%s",
            len(items_list), len(results), len(errors)
        )

        return results

    def _process_single(self, item: T, processor: Callable[[T, Any], R]) -> R:
        """Process a single item with connection from pool."""
        with get_connection(self.engine) as conn:
            return processor(item, conn)

    def bulk_insert(
        self,
        table: str,
        records: list[dict],
        on_duplicate: str | None = None,
    ) -> int:
        """
        Bulk insert records with automatic batching.

        Args:
            table: Table name
            records: List of record dictionaries
            on_duplicate: ON DUPLICATE KEY UPDATE clause (optional)

        Returns:
            Number of rows affected
        """
        if not records:
            return 0

        total = 0
        columns = list(records[0].keys())

        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]

            placeholders = ', '.join(f':{col}' for col in columns)
            columns_str = ', '.join(columns)

            sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

            if on_duplicate:
                sql += f" {on_duplicate}"

            with get_connection(self.engine) as conn:
                result = conn.execute(text(sql), batch)
                total += result.rowcount

            logger.debug(
                "event=bulk_insert_batch batch=%s/%s rows=%s",
                i // self.batch_size + 1,
                (len(records) + self.batch_size - 1) // self.batch_size,
                result.rowcount
            )

        return total

    def chunked_query(
        self,
        sql: str,
        params: dict | None = None,
        chunk_size: int = 1000,
    ):
        """
        Generator that yields query results in chunks to limit memory usage.

        Usage:
            for chunk in processor.chunked_query("SELECT * FROM large_table"):
                process_chunk(chunk)
        """
        offset = 0
        while True:
            chunk_sql = f"{sql} LIMIT {chunk_size} OFFSET {offset}"

            with get_connection(self.engine) as conn:
                result = conn.execute(text(chunk_sql), params or {})
                rows = [dict(row._mapping) for row in result]

            if not rows:
                break

            yield rows
            offset += chunk_size

            if len(rows) < chunk_size:
                break


def process_files_with_pool(
    files: list[str],
    process_func: Callable[[str], Any],
    max_workers: int = 4,
) -> dict:
    """
    High-level function for processing file batches.

    Example usage for the 700-file workload:
        results = process_files_with_pool(
            files=file_list,
            process_func=process_single_file,
            max_workers=4,
        )
    """
    processor = BatchProcessor(max_workers=max_workers)

    def wrapper(file_path: str, conn) -> dict:
        # Pass connection to processor if needed for DB operations
        return {"file": file_path, "result": process_func(file_path)}

    results = processor.process_items(files, wrapper)

    return {
        "total": len(files),
        "successful": len([r for r in results if r["result"] is not None]),
        "results": results,
    }
```

### 5.2 Background Worker Integration

Update worker patterns in `src/main_app/jobs_workers/`:

```python
"""Example integration in a background worker."""

from ..db.batch_processor import BatchProcessor
from ..db.engine_factory import get_background_engine


class FileProcessingWorker:
    """Worker that processes files with pooled database connections."""

    def __init__(self):
        self.engine = get_background_engine()
        self.processor = BatchProcessor(max_workers=4, batch_size=50)

    def run(self, file_list: list[str]) -> dict:
        """Process a batch of files."""
        # Process files with controlled concurrency
        results = self.processor.process_items(
            items=file_list,
            processor=self._process_file,
            error_handler=self._handle_error,
        )

        # Bulk insert results
        if results:
            self.processor.bulk_insert(
                table="processing_results",
                records=results,
                on_duplicate="ON DUPLICATE KEY UPDATE status=VALUES(status)",
            )

        return {"processed": len(results)}

    def _process_file(self, file_path: str, conn) -> dict:
        """Process a single file with database connection."""
        # Use conn for database operations
        # Connection is borrowed from pool and returned after
        result = perform_file_operation(file_path)

        # Insert intermediate result if needed
        conn.execute(
            text("UPDATE tasks SET progress = progress + 1 WHERE id = :id"),
            {"id": self.task_id}
        )

        return {"file": file_path, "status": "completed"}

    def _handle_error(self, file_path: str, exc: Exception):
        """Handle processing errors."""
        logger.error("event=file_process_error file=%s error=%s", file_path, exc)
```

---

## 6. Monitoring and Observability

### 6.1 Pool Metrics Logging

Add to `src/main_app/db/engine_factory.py`:

```python
import time
from functools import wraps


class PoolMonitor:
    """Monitor and log connection pool metrics."""

    def __init__(self, engine: Engine, name: str):
        self.engine = engine
        self.name = name
        self.last_log_time = 0
        self.log_interval = 60  # Log every 60 seconds

    def log_status(self, force: bool = False):
        """Log current pool status if interval has passed."""
        now = time.time()
        if not force and now - self.last_log_time < self.log_interval:
            return

        self.last_log_time = now
        pool = self.engine.pool

        logger.info(
            "event=pool_status "
            "name=%s "
            "size=%s "
            "checked_in=%s "
            "checked_out=%s "
            "overflow=%s "
            "utilization=%.1f%%",
            self.name,
            pool.size(),
            pool.checkedin(),
            pool.checkedout(),
            pool.overflow(),
            (pool.checkedout() / pool.size() * 100) if pool.size() > 0 else 0
        )

    def record_wait_time(self, wait_ms: float):
        """Record time spent waiting for connection."""
        logger.debug("event=pool_wait name=%s wait_ms=%.2f", self.name, wait_ms)


# Global monitors
_http_monitor: PoolMonitor | None = None
_background_monitor: PoolMonitor | None = None


def get_http_monitor() -> PoolMonitor:
    global _http_monitor
    if _http_monitor is None:
        _http_monitor = PoolMonitor(get_http_engine(), "http")
    return _http_monitor


def get_background_monitor() -> PoolMonitor:
    global _background_monitor
    if _background_monitor is None:
        _background_monitor = PoolMonitor(get_background_engine(), "background")
    return _background_monitor
```

### 6.2 Health Check Endpoint

Add to Flask routes:

```python
@app.route('/health/db')
def db_health_check():
    """Database connectivity and pool health check."""
    from sqlalchemy import text

    try:
        engine = get_http_engine()

        # Test connectivity
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()

        # Get pool stats
        pool = engine.pool
        return jsonify({
            "status": "healthy",
            "pool": {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
        }), 200

    except Exception as e:
        logger.error("event=health_check_failed error=%s", e)
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
```

### 6.3 Prometheus Metrics (Optional)

```python
"""Prometheus metrics for connection pool monitoring."""

try:
    from prometheus_client import Gauge, Histogram, Counter

    POOL_SIZE = Gauge('sqlalchemy_pool_size', 'Pool size', ['engine'])
    POOL_CHECKED_OUT = Gauge('sqlalchemy_pool_checked_out', 'Checked out connections', ['engine'])
    POOL_OVERFLOW = Gauge('sqlalchemy_pool_overflow', 'Overflow connections', ['engine'])
    CONNECTION_WAIT_TIME = Histogram('sqlalchemy_connection_wait_seconds', 'Time waiting for connection')
    CONNECTION_ERRORS = Counter('sqlalchemy_connection_errors_total', 'Connection errors', ['error_type'])

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


def update_prometheus_metrics(engine: Engine, name: str):
    """Update Prometheus metrics for an engine."""
    if not PROMETHEUS_AVAILABLE:
        return

    pool = engine.pool
    POOL_SIZE.labels(engine=name).set(pool.size())
    POOL_CHECKED_OUT.labels(engine=name).set(pool.checkedout())
    POOL_OVERFLOW.labels(engine=name).set(pool.overflow())
```

---

## 7. Migration Steps

### 7.1 Phase 1: Add SQLAlchemy Dependencies

Update `requirements.txt`:

```txt
# Existing dependencies
# ...

# SQLAlchemy with PyMySQL driver
sqlalchemy>=2.0.0
pymysql>=1.1.0  # Already present, ensure compatibility
```

### 7.2 Phase 2: Create Engine Factory (Parallel Implementation)

1. Create `src/main_app/db/engine_factory.py` (Section 4.1)
2. Create `src/main_app/db/db_sqlalchemy.py` (Section 4.3)
3. Run unit tests to ensure compatibility

### 7.3 Phase 3: Gradual Migration

Update `src/main_app/db/task_store_pymysql.py`:

```python
# Add import at top
from .db_sqlalchemy import DatabaseSQLAlchemy

class TaskStorePyMysql(CreateUpdateTask, StageStore, TasksListDB, DbUtils):
    """MySQL-backed task store with SQLAlchemy connection pooling."""

    def __init__(self, database_data: DbConfig, use_pooling: bool = True) -> None:
        if use_pooling:
            self.db = DatabaseSQLAlchemy(database_data)
        else:
            # Fallback to legacy for gradual migration
            from .db_class import Database
            self.db = Database(database_data)

        self._init_schema()
        super().__init__(self.db)
```

### 7.4 Phase 4: Background Worker Migration

Update job workers to use the background engine:

```python
# In each worker file
from ..db.engine_factory import get_background_engine

class SomeWorker:
    def __init__(self):
        self.engine = get_background_engine()
```

### 7.5 Phase 5: Remove Legacy Code

Once all components are migrated:

1. Remove `src/main_app/db/db_class.py`
2. Rename `TaskStorePyMysql` → `TaskStore`
3. Remove `use_pooling` fallback parameter
4. Update all imports

### 7.6 Migration Checklist

-   [ ] Add SQLAlchemy to requirements
-   [ ] Create engine factory module
-   [ ] Create compatibility wrapper
-   [ ] Update TaskStore to use new wrapper
-   [ ] Migrate HTTP routes (test each)
-   [ ] Migrate background workers
-   [ ] Update batch processing code
-   [ ] Add health check endpoint
-   [ ] Add monitoring/metrics
-   [ ] Load test in staging
-   [ ] Deploy to production
-   [ ] Monitor pool metrics
-   [ ] Remove legacy code

---

## 8. Risk Analysis

| Risk                             | Likelihood | Impact   | Mitigation                                                                                                                                                    |
| -------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SQL Syntax Incompatibility**   | Medium     | High     | SQLAlchemy uses named parameters (`:param`) vs PyMySQL positional (`%s`). The wrapper converts automatically, but complex queries may need manual adjustment. |
| **Transaction Behavior Changes** | Medium     | High     | SQLAlchemy defaults to autocommit=False. Explicit commit/rollback in context manager. Test all write operations.                                              |
| **Pool Exhaustion Under Load**   | Low        | High     | Monitor pool utilization. Scale pool_size/max_overflow based on metrics. Add circuit breaker if needed.                                                       |
| **Connection Leaks**             | Low        | Critical | Always use context managers (`with` statements). Enable `pool_pre_ping` to detect stale connections.                                                          |
| **Performance Regression**       | Low        | Medium   | Connection pooling adds overhead. Benchmark before/after. Adjust pool settings as needed.                                                                     |
| **Background Worker Starvation** | Medium     | High     | Use separate engine for background work with isolated pool.                                                                                                   |
| **Migration Rollback**           | Low        | High     | Keep legacy code during migration. Feature flag to switch between implementations.                                                                            |

### Rollback Strategy

```python
# Feature flag in config
USE_SQLALCHEMY_POOLING = os.getenv('USE_SQLALCHEMY_POOLING', 'true').lower() == 'true'

# In TaskStore
if USE_SQLALCHEMY_POOLING:
    from .db_sqlalchemy import DatabaseSQLAlchemy
    self.db = DatabaseSQLAlchemy(database_data)
else:
    from .db_class import Database
    self.db = Database(database_data)
```

---

## 9. Production Hardening Checklist

### 9.1 Pre-Deployment

-   [ ] Load test with 2× expected traffic
-   [ ] Verify pool utilization stays under 80%
-   [ ] Test error 1203 scenario (artificially limit connections)
-   [ ] Verify graceful degradation when pool exhausted
-   [ ] Test background worker isolation
-   [ ] Confirm all database queries work with SQLAlchemy
-   [ ] Validate transaction behavior for writes

### 9.2 Configuration

-   [ ] Set `pool_recycle` < MySQL `wait_timeout`
-   [ ] Set `pool_pre_ping = True`
-   [ ] Configure `pool_timeout` for graceful failure
-   [ ] Set appropriate `pool_size` and `max_overflow`
-   [ ] Use separate engines for HTTP and background work
-   [ ] Configure connection timeouts appropriately

### 9.3 Monitoring

-   [ ] Log pool metrics at regular intervals
-   [ ] Alert on high pool utilization (>80%)
-   [ ] Alert on connection wait time (>1s)
-   [ ] Monitor MySQL connection count
-   [ ] Set up error 1203 alerting
-   [ ] Health check endpoint returning pool stats

### 9.4 Security

-   [ ] Database credentials in environment variables
-   [ ] No SQL logging in production (`echo=False`)
-   [ ] Connection timeouts configured
-   [ ] SSL/TLS for database connections if available
-   [ ] Review SQL injection protections

### 9.5 Documentation

-   [ ] Runbook for connection pool issues
-   [ ] Document pool sizing formula
-   [ ] Migration guide for developers
-   [ ] Troubleshooting guide

---

## Appendix A: Quick Reference

### Pool Configuration Matrix

| Environment | Workers | Pods | pool_size | max_overflow | pool_recycle |
| ----------- | ------- | ---- | --------- | ------------ | ------------ |
| Local Dev   | 1       | 1    | 5         | 5            | 3600         |
| Staging     | 3       | 1    | 3         | 2            | 3600         |
| Production  | 7       | 2    | 3         | 2            | 3600         |
| Background  | 4       | 2    | 4         | 4            | 3600         |

### Common Issues and Solutions

| Symptom                 | Cause                      | Solution                                      |
| ----------------------- | -------------------------- | --------------------------------------------- |
| Error 1203 persists     | Pool too large             | Reduce `pool_size` and `max_overflow`         |
| Slow requests           | Pool exhausted, waiting    | Increase `pool_size` or add caching           |
| Stale connection errors | MySQL timeout              | Enable `pool_pre_ping`, reduce `pool_recycle` |
| Memory growth           | Connections not returned   | Check for missing `with` statements           |
| Background tasks slow   | HTTP workers starving pool | Use separate background engine                |

### Connection String Reference

```python
# Standard Toolforge URL
mysql+pymysql://USER:PASSWORD@tools.db.svc.eqiad.wmflabs/DB_NAME?charset=utf8mb4

# With SSL (if required)
mysql+pymysql://USER:PASSWORD@HOST/DB_NAME?ssl_ca=/etc/ssl/certs/ca-certificates.crt
```

---

## Document Information

-   **Version**: 1.0
-   **Author**: Backend Architecture Team
-   **Date**: 2026-02-26
-   **Review Cycle**: Quarterly
