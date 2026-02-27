from __future__ import annotations

import logging
import random
import threading
import time
from typing import Any, Iterable, Sequence

import pymysql
from sqlalchemy import text

from ..config import DbConfig
from .engine_factory import db_connection, get_http_engine, get_bg_engine

logger = logging.getLogger(__name__)


class MaxUserConnectionsError(Exception):
    pass


def _convert_params(params: Any) -> dict[str, Any] | list[dict[str, Any]] | None:
    """
    Convert PyMySQL-style parameters to SQLAlchemy 2.0 format.
    
    SQLAlchemy 2.0 with text() expects:
    - dict for single-row named parameters: {"param1": value1, "param2": value2}
    - list of dicts for executemany: [{"param1": val1}, {"param1": val2}]
    
    This helper converts tuple/list params to dict format with auto-generated keys.
    """
    if params is None:
        return None
    
    # If it's already a dict, return as-is
    if isinstance(params, dict):
        return params
    
    # If it's a tuple or list, convert to dict with positional keys
    if isinstance(params, (tuple, list)):
        return {f"p{i}": v for i, v in enumerate(params)}
    
    # Single value - wrap in dict
    return {"p0": params}


def _convert_sql(sql: str, params: Any) -> tuple[str, dict[str, Any] | None]:
    """
    Convert PyMySQL-style SQL (%s placeholders) to SQLAlchemy named parameters.
    
    Returns:
        Tuple of (converted_sql, converted_params)
    """
    converted_params = _convert_params(params)
    
    if converted_params is None:
        return sql, None
    
    # Replace %s with :p0, :p1, etc.
    import re
    param_names = list(converted_params.keys())
    param_index = [0]
    
    def replace_placeholder(match):
        idx = param_index[0]
        if idx < len(param_names):
            param_index[0] += 1
            return f":{param_names[idx]}"
        return match.group(0)  # Should not happen
    
    # Replace %s placeholders with :pN named parameters
    converted_sql = re.sub(r"%s", replace_placeholder, sql)
    
    return converted_sql, converted_params


class Database:
    """Thin wrapper around SQLAlchemy engine with convenience helpers.
    
    Uses connection pooling via engine_factory to avoid max_user_connections errors.
    Maintains backward compatibility with the original PyMySQL-based interface.
    """

    RETRYABLE_ERROR_CODES = {2006, 2013, 2014, 2017, 2018, 2055}
    MAX_RETRIES = 3
    BASE_BACKOFF = 0.2

    def __init__(self, database_data: DbConfig, use_bg_engine: bool = False):
        """
        Create a Database wrapper using SQLAlchemy connection pooling.

        Parameters:
            database_data (DbConfig): Configuration object with attributes `db_host`, `db_name`, `db_user`, and `db_password`.
            use_bg_engine (bool): If True, use the background engine pool (for batch jobs).
        """
        self._use_bg_engine = use_bg_engine
        self._engine = None  # Lazy initialization
        self._lock = threading.RLock()
        # Keep these for backward compatibility (some code may access them)
        self.host = database_data.db_host
        self.dbname = database_data.db_name
        self.user = database_data.db_user
        self.password = database_data.db_password
        self.credentials = {"user": self.user, "password": self.password}
        self.connection: Any | None = None  # Not used with pooling, but kept for compatibility

    def _get_engine(self):
        """Get the appropriate engine (lazy initialization)."""
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    if self._use_bg_engine:
                        self._engine = get_bg_engine()
                    else:
                        self._engine = get_http_engine()
        return self._engine

    def _connect(self) -> None:
        """No-op for compatibility - connections are managed by the pool."""
        pass

    def _ensure_connection(self) -> None:
        """No-op for compatibility - pool handles connection health."""
        pass

    def _close_connection(self) -> None:
        """No-op for compatibility - connections are returned to pool automatically."""
        pass

    def close(self) -> None:
        """No-op for compatibility - pool manages connections."""
        pass

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Retry utilities
    # ------------------------------------------------------------------
    def _exception_code(self, exc: BaseException) -> int | None:
        """Extract MySQL error code from exception.
        
        Handles both raw PyMySQL exceptions and SQLAlchemy-wrapped exceptions.
        """
        # Handle SQLAlchemy wrapped exceptions
        if hasattr(exc, "__cause__") and exc.__cause__ is not None:
            inner = exc.__cause__
            if isinstance(inner, (pymysql.err.OperationalError, pymysql.err.InterfaceError)):
                try:
                    return inner.args[0]
                except (IndexError, TypeError):
                    return None
        
        # Handle raw PyMySQL exceptions
        if isinstance(exc, (pymysql.err.OperationalError, pymysql.err.InterfaceError)):
            try:
                code = exc.args[0]
                return code
            except (IndexError, TypeError):
                return None
        return None

    def _should_retry(self, exc: BaseException) -> bool:
        code = self._exception_code(exc)
        return code in self.RETRYABLE_ERROR_CODES

    def _compute_backoff(self, attempt: int) -> float:
        return self.BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.1)

    def _log_retry(self, event: str, attempt: int, exc: BaseException, elapsed_ms: int) -> None:
        code = exc.args[0] if getattr(exc, "args", None) else None
        logger.debug("event=%s attempt=%s code=%s elapsed_ms=%s", event, attempt, code, elapsed_ms)

    def _execute_with_retry(
        self,
        operation,
        sql_query: str,
        params: Any,
        *,
        timeout_override: float | None = None,
        readonly: bool = False,
    ):
        last_exc: BaseException | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                with db_connection(self._get_engine(), readonly=readonly) as conn:
                    if timeout_override is not None:
                        milliseconds = max(int(timeout_override * 1000), 1)
                        conn.execute(text("SET SESSION MAX_EXECUTION_TIME=:ms"), {"ms": milliseconds})
                    try:
                        result = operation(conn, sql_query, params)
                        return result
                    finally:
                        if timeout_override is not None:
                            conn.execute(text("SET SESSION MAX_EXECUTION_TIME=0"))
            except Exception as exc:  # noqa: PERF203 - retries require broad catch
                elapsed_ms = int((time.monotonic() - start) * 1000)
                if self._should_retry(exc) and attempt < self.MAX_RETRIES:
                    self._log_retry("db_retry", attempt, exc, elapsed_ms)
                    time.sleep(self._compute_backoff(attempt))
                    last_exc = exc
                    continue

                if isinstance(exc, pymysql.MySQLError):
                    code = self._exception_code(exc)
                    if code == 1203:
                        logger.error("event=max_user_connections")
                        raise MaxUserConnectionsError from exc
                    self._log_retry("db_retry_failed", attempt, exc, elapsed_ms)
                last_exc = exc
                break

        assert last_exc is not None  # for mypy
        raise last_exc

    def execute_query(
        self,
        sql_query: str,
        params: Any = None,
        *,
        timeout_override: float | None = None,
    ):
        """Execute a statement and return rows for SELECTs or rowcount for writes."""

        def _op(conn, sql, op_params):
            # Convert PyMySQL-style %s to SQLAlchemy named parameters
            conv_sql, conv_params = _convert_sql(sql, op_params)
            result = conn.execute(text(conv_sql), conv_params or {})
            # Check if this is a SELECT-like query that returns rows
            if result.returns_rows:
                rows = result.mappings().all()
                return [dict(row) for row in rows]
            return result.rowcount

        return self._execute_with_retry(
            _op,
            sql_query,
            params,
            timeout_override=timeout_override,
            readonly=False,
        )

    def fetch_query(
        self,
        sql_query: str,
        params: Any = None,
        *,
        timeout_override: float | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query and return all fetched rows as dictionaries."""

        def _op(conn, sql, op_params):
            # Convert PyMySQL-style %s to SQLAlchemy named parameters
            conv_sql, conv_params = _convert_sql(sql, op_params)
            result = conn.execute(text(conv_sql), conv_params or {})
            rows = result.mappings().all()
            return [dict(row) for row in rows]

        result = self._execute_with_retry(
            _op,
            sql_query,
            params,
            timeout_override=timeout_override,
            readonly=True,
        )
        return list(result or [])

    def execute_many(
        self,
        sql_query: str,
        params_seq: Iterable[Any],
        batch_size: int = 1000,
        *,
        timeout_override: float | None = None,
    ) -> int:
        """Bulk-execute a SQL statement with retry and chunk splitting."""

        params_list = list(params_seq)
        if not params_list:
            return 0

        def _op(conn, sql, _params_list):
            return self._execute_many_batches(conn, sql, params_list, batch_size)

        result = self._execute_with_retry(
            _op,
            sql_query,
            params_list,
            timeout_override=timeout_override,
            readonly=False,
        )
        return int(result)

    def _execute_many_batches(
        self,
        conn,
        sql_query: str,
        params_list: Sequence[Any],
        batch_size: int,
    ) -> int:
        total = 0
        index = 0
        while index < len(params_list):
            batch = params_list[index : index + batch_size]
            total += self._execute_many_batch(conn, sql_query, batch)
            index += batch_size
        return total

    def _execute_many_batch(self, conn, sql_query: str, batch: Sequence[Any]) -> int:
        if not batch:
            return 0
        try:
            # Convert SQL and params for SQLAlchemy 2.0
            # For executemany, convert list of tuples to list of dicts
            conv_sql, first_params = _convert_sql(sql_query, batch[0] if batch else None)
            # Convert all items in batch to dicts
            if isinstance(batch[0], (tuple, list)):
                param_dicts = [{f"p{i}": v for i, v in enumerate(item)} for item in batch]
            else:
                param_dicts = list(batch)
            result = conn.execute(text(conv_sql), param_dicts)
            return result.rowcount
        except (pymysql.err.OperationalError, pymysql.err.InterfaceError):
            if len(batch) <= 1:
                raise
            mid = (len(batch) + 1) // 2
            return self._execute_many_batch(conn, sql_query, batch[:mid]) + self._execute_many_batch(
                conn, sql_query, batch[mid:]
            )

    def fetch_query_safe(self, sql_query, params=None, *, timeout_override: float | None = None):
        """Return all rows for a query while converting SQL failures into logs."""
        try:
            return self.fetch_query(sql_query, params, timeout_override=timeout_override)
        except pymysql.MySQLError as e:
            logger.error("event=db_fetch_failed sql=%s error=%s", sql_query, e)
            logger.debug(f"fetch_query - SQL error: {e}\n{sql_query}, params:")
            logger.debug(params)
            return []

    def execute_query_safe(self, sql_query, params=None, *, timeout_override: float | None = None):
        """Execute a statement while swallowing PyMySQL exceptions."""
        try:
            return self.execute_query(sql_query, params, timeout_override=timeout_override)
        except pymysql.MySQLError as e:
            logger.error("event=db_execute_failed sql=%s error=%s", sql_query, e)
            logger.debug(f"execute_query - SQL error: {e}\n{sql_query}, params:")
            logger.debug(params)
            if sql_query.strip().lower().startswith("select"):
                return []
            return 0
