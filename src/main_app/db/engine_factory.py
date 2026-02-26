"""SQLAlchemy Engine factory for connection pooling."""

from __future__ import annotations

import logging
import os
import time
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

# Feature flag for gradual migration
USE_SQLALCHEMY_POOLING = os.getenv("USE_SQLALCHEMY_POOLING", "true").lower() == "true"


class DatabaseError(Exception):
    """Wrapper for database-related errors."""
    pass


class MaxUserConnectionsError(DatabaseError):
    """Raised when MySQL max_user_connections is exceeded."""
    pass


def _build_connection_url(db_config: DbConfig) -> str:
    """Construct MySQL connection URL from DbConfig."""
    # URL format: mysql+pymysql://user:password@host/database
    return (
        f"mysql+pymysql://{db_config.db_user}:{db_config.db_password}"
        f"@{db_config.db_host}/{db_config.db_name}"
        f"?charset=utf8mb4"
    )


def _get_pool_config() -> dict:
    """Get pool configuration from environment or use defaults."""
    return {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "3")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "2")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    }


def _get_background_pool_config() -> dict:
    """Get background worker pool configuration."""
    return {
        "pool_size": int(os.getenv("DB_BG_POOL_SIZE", "4")),
        "max_overflow": int(os.getenv("DB_BG_MAX_OVERFLOW", "4")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_timeout": int(os.getenv("DB_BG_POOL_TIMEOUT", "60")),
    }


def create_http_engine(db_config: DbConfig | None = None) -> Engine:
    """
    Create SQLAlchemy Engine optimized for HTTP request handling.

    Uses smaller pool size to share connections across many concurrent requests.
    """
    global _http_engine

    if _http_engine is not None:
        return _http_engine

    config = db_config or settings.database_data
    pool_config = _get_pool_config()

    _http_engine = create_engine(
        _build_connection_url(config),
        poolclass=QueuePool,
        pool_size=pool_config["pool_size"],
        max_overflow=pool_config["max_overflow"],
        pool_recycle=pool_config["pool_recycle"],
        pool_pre_ping=True,
        pool_timeout=pool_config["pool_timeout"],
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
        "pool_size=%s max_overflow=%s pool_recycle=%s pool_timeout=%s",
        pool_config["pool_size"],
        pool_config["max_overflow"],
        pool_config["pool_recycle"],
        pool_config["pool_timeout"],
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
    pool_config = _get_background_pool_config()

    _background_engine = create_engine(
        _build_connection_url(config),
        poolclass=QueuePool,
        pool_size=pool_config["pool_size"],
        max_overflow=pool_config["max_overflow"],
        pool_recycle=pool_config["pool_recycle"],
        pool_pre_ping=True,
        pool_timeout=pool_config["pool_timeout"],
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "read_timeout": 300,  # Longer timeout for batch operations
            "write_timeout": 300,
            "init_command": "SET time_zone = '+00:00'",
        },
    )

    logger.info(
        "event=background_engine_created "
        "pool_size=%s max_overflow=%s pool_recycle=%s pool_timeout=%s",
        pool_config["pool_size"],
        pool_config["max_overflow"],
        pool_config["pool_recycle"],
        pool_config["pool_timeout"],
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
    start_time = time.time()
    try:
        yield conn
        conn.commit()
    except SQLAlchemyError as e:
        conn.rollback()
        # Re-raise SQLAlchemy errors directly - let caller handle specific types
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        wait_time = (time.time() - start_time) * 1000
        if wait_time > 1000:  # Log slow connections
            logger.warning("event=slow_db_connection wait_ms=%.2f", wait_time)
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
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PoolMonitor:
    """Monitor and log connection pool metrics."""

    def __init__(self, engine: Engine, name: str):
        self.engine = engine
        self.name = name
        self.last_log_time = 0
        self.log_interval = 60  # Log every 60 seconds

    def log_status(self, force: bool = False) -> dict[str, Any]:
        """Log current pool status if interval has passed."""
        now = time.time()
        if not force and now - self.last_log_time < self.log_interval:
            return {}

        self.last_log_time = now
        pool = self.engine.pool

        stats = {
            "name": self.name,
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "utilization": (
                (pool.checkedout() / pool.size() * 100) if pool.size() > 0 else 0
            ),
        }

        logger.info(
            "event=pool_status "
            "name=%s "
            "size=%s "
            "checked_in=%s "
            "checked_out=%s "
            "overflow=%s "
            "utilization=%.1f%%",
            stats["name"],
            stats["size"],
            stats["checked_in"],
            stats["checked_out"],
            stats["overflow"],
            stats["utilization"],
        )

        return stats


# Global monitors
_http_monitor: PoolMonitor | None = None
_background_monitor: PoolMonitor | None = None


def get_http_monitor() -> PoolMonitor:
    """Get or create the HTTP engine monitor."""
    global _http_monitor
    if _http_monitor is None:
        _http_monitor = PoolMonitor(get_http_engine(), "http")
    return _http_monitor


def get_background_monitor() -> PoolMonitor:
    """Get or create the background engine monitor."""
    global _background_monitor
    if _background_monitor is None:
        _background_monitor = PoolMonitor(get_background_engine(), "background")
    return _background_monitor


def log_all_pool_status(force: bool = False) -> dict[str, dict[str, Any]]:
    """Log status of all connection pools."""
    return {
        "http": get_http_monitor().log_status(force),
        "background": get_background_monitor().log_status(force),
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
            result = conn.execute(text("SELECT 1"))
            result.scalar()

        # Get pool stats
        pool = eng.pool
        return {
            "status": "healthy",
            "pool": {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            },
        }
    except Exception as e:
        logger.error("event=connection_health_check_failed error=%s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
        }
