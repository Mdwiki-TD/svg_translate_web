"""SQLAlchemy-based database wrapper compatible with existing Database class interface."""

from __future__ import annotations

import logging
import random
import re
import time
from typing import Any, Iterable, Sequence

import pymysql
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from ..config import DbConfig
from .engine_factory import (
    DatabaseError,
    MaxUserConnectionsError,
    get_connection,
    get_http_engine,
    get_background_engine,
)

logger = logging.getLogger(__name__)


class DatabaseSQLAlchemy:
    """
    SQLAlchemy-based database wrapper compatible with legacy Database interface.

    Uses connection pooling instead of creating new connections per operation.
    """

    RETRYABLE_ERROR_CODES = {2006, 2013, 2014, 2017, 2018, 2055, 1203}
    MAX_RETRIES = 3
    BASE_BACKOFF = 0.2

    def __init__(
        self,
        database_data: DbConfig,
        use_background_engine: bool = False,
    ):
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
                self._engine = get_background_engine()
            else:
                self._engine = get_http_engine()
        return self._engine

    def _exception_code(self, exc: BaseException) -> int | None:
        """Extract MySQL error code from exception."""
        if isinstance(exc, SQLAlchemyError):
            if hasattr(exc, "orig") and exc.orig:
                orig = exc.orig
                if hasattr(orig, "args") and orig.args:
                    try:
                        return int(orig.args[0])
                    except (IndexError, TypeError, ValueError):
                        pass
        return None

    def _should_retry(self, exc: BaseException) -> bool:
        """Determine if error is retryable."""
        # Never retry integrity errors (duplicate key, etc.)
        if isinstance(exc, IntegrityError):
            return False
        code = self._exception_code(exc)
        return code in self.RETRYABLE_ERROR_CODES

    def _is_integrity_error(self, exc: BaseException) -> bool:
        """Check if exception is an integrity error."""
        return isinstance(exc, IntegrityError)

    def _compute_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        return self.BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.1)

    def _execute_with_retry(
        self,
        operation,
        sql_query: str,
        params: Any = None,
    ):
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

                # Integrity errors should be re-raised immediately for caller handling
                if self._is_integrity_error(exc):
                    logger.debug("event=integrity_error error=%s", exc)
                    # Re-raise as pymysql IntegrityError for compatibility
                    orig = exc.orig if hasattr(exc, "orig") else exc
                    raise pymysql.err.IntegrityError(
                        orig.args[0] if hasattr(orig, "args") else 1062,
                        str(exc),
                    ) from exc

                # Special handling for max_user_connections
                if code == 1203:
                    logger.error(
                        "event=max_user_connections_exceeded attempt=%s", attempt
                    )
                    if attempt >= self.MAX_RETRIES:
                        raise MaxUserConnectionsError(
                            "MySQL max_user_connections exceeded"
                        ) from exc
                    # Exponential backoff for 1203
                    time.sleep(self._compute_backoff(attempt) * 2)
                    last_exc = exc
                    continue

                if self._should_retry(exc) and attempt < self.MAX_RETRIES:
                    logger.debug(
                        "event=db_retry attempt=%s code=%s elapsed_ms=%s",
                        attempt,
                        code,
                        elapsed_ms,
                    )
                    time.sleep(self._compute_backoff(attempt))
                    last_exc = exc
                    continue

                logger.error(
                    "event=db_error attempt=%s code=%s elapsed_ms=%s error=%s",
                    attempt,
                    code,
                    elapsed_ms,
                    exc,
                )
                last_exc = exc
                break

        assert last_exc is not None
        raise last_exc

    def _convert_placeholders(self, sql: str) -> str:
        """Convert PyMySQL %s placeholders to SQLAlchemy named parameters."""
        count = [0]

        def replace(match):
            result = f":p{count[0]}"
            count[0] += 1
            return result

        return re.sub(r"%s", replace, sql)

    def _convert_params(self, params: Any) -> dict | None:
        """Convert PyMySQL-style params to SQLAlchemy named params."""
        if params is None:
            return None
        if isinstance(params, dict):
            return params
        if isinstance(params, (list, tuple)):
            return {f"p{i}": v for i, v in enumerate(params)}
        return {"p0": params}

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
            # Detect SQL type
            sql_upper = sql.strip().upper()
            is_select = sql_upper.startswith("SELECT")
            is_show = sql_upper.startswith("SHOW")

            # Convert placeholders
            converted_sql = self._convert_placeholders(sql)
            converted_params = self._convert_params(op_params)

            # Handle timeout override
            if timeout_override is not None:
                milliseconds = max(int(timeout_override * 1000), 1)
                conn.execute(
                    text("SET SESSION MAX_EXECUTION_TIME=:timeout"),
                    {"timeout": milliseconds},
                )

            try:
                result = conn.execute(text(converted_sql), converted_params or {})

                if is_select or is_show or result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return result.rowcount
            finally:
                if timeout_override is not None:
                    try:
                        conn.execute(
                            text("SET SESSION MAX_EXECUTION_TIME=0"),
                        )
                    except Exception:
                        pass

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
            converted_sql = self._convert_placeholders(sql)
            converted_params = self._convert_params(op_params)

            # Handle timeout override
            if timeout_override is not None:
                milliseconds = max(int(timeout_override * 1000), 1)
                conn.execute(
                    text("SET SESSION MAX_EXECUTION_TIME=:timeout"),
                    {"timeout": milliseconds},
                )

            try:
                result = conn.execute(text(converted_sql), converted_params or {})
                return [dict(row._mapping) for row in result]
            finally:
                if timeout_override is not None:
                    try:
                        conn.execute(text("SET SESSION MAX_EXECUTION_TIME=0"))
                    except Exception:
                        pass

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
            converted_sql = self._convert_placeholders(sql)

            for i in range(0, len(_params_list), batch_size):
                batch = _params_list[i : i + batch_size]

                # Convert batch params
                if batch and isinstance(batch[0], (list, tuple)):
                    dict_batch = [
                        {f"p{j}": v for j, v in enumerate(row)} for row in batch
                    ]
                else:
                    dict_batch = [{"p0": row} for row in batch]

                # Handle timeout
                if timeout_override is not None:
                    milliseconds = max(int(timeout_override * 1000), 1)
                    conn.execute(
                        text("SET SESSION MAX_EXECUTION_TIME=:timeout"),
                        {"timeout": milliseconds},
                    )

                try:
                    result = conn.execute(text(converted_sql), dict_batch)
                    total += result.rowcount
                finally:
                    if timeout_override is not None:
                        try:
                            conn.execute(text("SET SESSION MAX_EXECUTION_TIME=0"))
                        except Exception:
                            pass

            return total

        return self._execute_with_retry(_op, sql_query, params_list)

    def fetch_query_safe(
        self,
        sql_query: str,
        params: Any = None,
        *,
        timeout_override: float | None = None,
    ):
        """Execute query with error suppression."""
        try:
            return self.fetch_query(sql_query, params, timeout_override=timeout_override)
        except SQLAlchemyError as e:
            logger.error("event=db_fetch_failed sql=%s error=%s", sql_query, e)
            return []

    def execute_query_safe(
        self,
        sql_query: str,
        params: Any = None,
        *,
        timeout_override: float | None = None,
    ):
        """Execute statement with error suppression."""
        try:
            return self.execute_query(
                sql_query, params, timeout_override=timeout_override
            )
        except SQLAlchemyError as e:
            logger.error("event=db_execute_failed sql=%s error=%s", sql_query, e)
            if sql_query.strip().lower().startswith("select"):
                return []
            return 0

    def close(self) -> None:
        """No-op for compatibility; connections managed by pool."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.close()
