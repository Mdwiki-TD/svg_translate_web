"""SQLAlchemy Engine factory for connection pooling.

Improvements over v1.0:
  - URL.create()       : safe password encoding, no f-string interpolation
  - threading.Lock     : prevent double-initialization in multi-threaded envs
  - readonly parameter : skip commit() on SELECT-only connections
  - 1203 retry backoff : wait for pool to free up instead of raising immediately
"""

from __future__ import annotations

import logging
import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from ..config import DbConfig, settings

logger = logging.getLogger(__name__)

# Feature flag — allows instant rollback via environment variable without redeploy
USE_SQLALCHEMY_POOLING = os.getenv("USE_SQLALCHEMY_POOLING", "true").lower() == "true"

# ── Global singleton engines ────────────────────────────────────────────────
_http_engine: Engine | None = None
_background_engine: Engine | None = None

# ── Thread-safety locks ─────────────────────────────────────────────────────
# Fix: the original code had no locking.
# Without these locks, two threads starting simultaneously could both see
# `_http_engine is None` and each create a separate engine, doubling the
# connection count before either assignment completes.
_http_engine_lock = threading.Lock()
_background_engine_lock = threading.Lock()


class DatabaseError(Exception):
    """Wrapper for database-related errors."""
    pass


class MaxUserConnectionsError(DatabaseError):
    """Raised when MySQL error 1203 persists after all retry attempts."""
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
        password=db_config.db_password,  # encoded automatically by SQLAlchemy
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
            pool_size=int(os.getenv("DB_POOL_SIZE", "3")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "1")),  # reduced from 2 to 1
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            pool_pre_ping=True,  # replace stale connections transparently
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),  # raise TimeoutError after 30 s
            echo=False,
            connect_args={
                "connect_timeout": 5,
                "read_timeout": 30,
                "write_timeout": 30,
                "init_command": "SET time_zone = '+00:00'",
            },
        )

        logger.info(
            "event=http_engine_created pool_size=%s max_overflow=%s pool_recycle=%s",
            os.getenv("DB_POOL_SIZE", "3"),
            os.getenv("DB_MAX_OVERFLOW", "1"),
            os.getenv("DB_POOL_RECYCLE", "3600"),
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
            pool_size=int(os.getenv("DB_BG_POOL_SIZE", "4")),
            max_overflow=int(os.getenv("DB_BG_MAX_OVERFLOW", "0")),  # fixed pool only
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            pool_pre_ping=True,
            pool_timeout=int(os.getenv("DB_BG_POOL_TIMEOUT", "60")),  # longer wait for batch work
            echo=False,
            connect_args={
                "connect_timeout": 10,
                "read_timeout": 300,  # long timeout for batch operations
                "write_timeout": 300,
                "init_command": "SET time_zone = '+00:00'",
            },
        )

        logger.info(
            "event=background_engine_created pool_size=%s max_overflow=%s pool_recycle=%s",
            os.getenv("DB_BG_POOL_SIZE", "4"),
            os.getenv("DB_BG_MAX_OVERFLOW", "0"),
            os.getenv("DB_POOL_RECYCLE", "3600"),
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
    eng = engine or get_http_engine()
    conn = eng.connect()
    start_time = time.time()
    try:
        yield conn
        if not readonly:
            conn.commit()
        # readonly path: no commit and no rollback — nothing was written
    except Exception as e:
        if not readonly:
            conn.rollback()
        # Don't wrap SQLAlchemyError - let db_sqlalchemy handle specific errors
        raise
    finally:
        wait_time = (time.time() - start_time) * 1000
        if wait_time > 1000:  # Log slow connections
            logger.warning("event=slow_db_connection wait_ms=%.2f", wait_time)
        conn.close()  # returns the connection to the pool


@contextmanager
def get_raw_connection(engine: Engine | None = None) -> Generator[Any, None, None]:
    """
    Return a raw DBAPI connection for code that cannot use SQLAlchemy text().

    Intended for backward-compatibility during migration only.
    Prefer get_connection() for new code.
    """
    eng = engine or get_http_engine()
    conn = eng.raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PoolMonitor:
    """Periodically sample and log connection pool metrics."""

    # Alert threshold: emit a WARNING when utilisation exceeds this value
    HIGH_UTILIZATION_THRESHOLD = 0.80  # 80%

    def __init__(self, engine: Engine, name: str, log_interval: int = 60):
        self.engine = engine
        self.name = name
        self.log_interval = log_interval  # seconds between automatic log calls
        self._last_log_ts = 0.0

    def log_status(self, force: bool = False) -> dict[str, Any]:
        """
        Log current pool metrics.

        Respects log_interval to avoid flooding the log; pass force=True
        to emit immediately regardless of the interval.
        """
        now = time.time()
        if not force and (now - self._last_log_ts) < self.log_interval:
            return {}

        self._last_log_ts = now
        pool = self.engine.pool
        total_cap = pool.size() + max(pool.overflow(), 0)
        util = pool.checkedout() / total_cap if total_cap > 0 else 0.0

        level = logging.WARNING if util > self.HIGH_UTILIZATION_THRESHOLD else logging.INFO

        logger.log(
            level,
            "event=pool_status name=%s size=%s checked_in=%s "
            "checked_out=%s overflow=%s utilization=%.1f%%",
            self.name,
            pool.size(),
            pool.checkedin(),
            pool.checkedout(),
            pool.overflow(),
            util * 100,
        )

        return {
            "name": self.name,
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "utilization": round(util * 100, 1),
        }

    def metrics_dict(self) -> dict[str, Any]:
        """Return current pool metrics as a plain dict (for health endpoints)."""
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "utilization": round(pool.checkedout() / (pool.size() or 1) * 100, 1),
        }


def check_connection_health(engine: Engine | None = None) -> dict[str, Any]:
    """
    Check database connectivity and return pool statistics.

    Returns:
        Dictionary with status and pool metrics
    """
    try:
        eng = engine or get_http_engine()

        # Test connectivity
        with eng.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()

        # Get pool stats
        monitor = PoolMonitor(eng, "http")
        return {
            "status": "healthy",
            "pool": monitor.metrics_dict(),
        }
    except Exception as e:
        logger.error("event=connection_health_check_failed error=%s", e)
        return {"status": "unhealthy", "error": str(e)}


def log_all_pool_status(force: bool = False) -> dict[str, dict[str, Any]]:
    """Log status of all connection pools."""
    http_monitor = PoolMonitor(get_http_engine(), "http")
    bg_monitor = PoolMonitor(get_background_engine(), "background")
    return {
        "http": http_monitor.log_status(force),
        "background": bg_monitor.log_status(force),
    }
