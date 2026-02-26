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

import pymysql
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..config import DbConfig
from .engine_factory import (
    DatabaseError,
    MaxUserConnectionsError,
    get_connection,
    get_http_engine,
    get_background_engine,
)

logger = logging.getLogger(__name__)

# Pre-compiled once at import time — avoids re-compiling per query call
_PLACEHOLDER_RE = re.compile(r"%s")


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
    MAX_RETRIES = 3
    BASE_BACKOFF = 0.2  # seconds

    # Retry settings specifically for error 1203 (max_user_connections exceeded).
    # Fix: the original code raised 1203 immediately.  In practice the pool
    # releases a connection within a few seconds, so retrying is almost always
    # successful and far cheaper than surfacing the error to users.
    ERROR_1203_MAX_RETRIES = 3
    ERROR_1203_BASE_BACKOFF = 1.0  # longer base — connections free up slowly

    def __init__(
        self,
        database_data: DbConfig,
        use_background_engine: bool = False,
    ):
        self.db_config = database_data
        self.use_background_engine = use_background_engine
        self._engine = None

    @property
    def engine(self):
        """Lazy-load the appropriate engine on first access."""
        if self._engine is None:
            if self.use_background_engine:
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
        self,
        sql: str,
        params: Any,
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
            return sql, params  # already named — nothing to convert

        if isinstance(params, (list, tuple)):
            counter = iter(range(len(params)))
            converted = _PLACEHOLDER_RE.sub(lambda _: f":p{next(counter)}", sql)
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
                code = self._exception_code(exc)

                # ── Error 1203: wait for a pool slot to become free ──────────
                if code == 1203:
                    if attempt <= self.ERROR_1203_MAX_RETRIES:
                        wait = self._compute_backoff(
                            attempt, self.ERROR_1203_BASE_BACKOFF
                        )
                        logger.warning(
                            "event=max_user_connections_exceeded "
                            "attempt=%s/%s wait_s=%.2f — retrying",
                            attempt,
                            self.ERROR_1203_MAX_RETRIES,
                            wait,
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

                # ── Integrity errors: re-raise immediately for caller handling ─
                if isinstance(exc, IntegrityError):
                    logger.debug("event=integrity_error error=%s", exc)
                    # Re-raise as pymysql IntegrityError for compatibility
                    orig = exc.orig if hasattr(exc, "orig") else exc
                    raise pymysql.err.IntegrityError(
                        orig.args[0] if hasattr(orig, "args") else 1062,
                        str(exc),
                    ) from exc

                # ── Retryable connection errors ──────────────────────────────
                if code in self.RETRYABLE_ERROR_CODES and attempt < self.MAX_RETRIES:
                    wait = self._compute_backoff(attempt)
                    logger.debug(
                        "event=db_retry attempt=%s code=%s "
                        "elapsed_ms=%s wait_s=%.2f",
                        attempt,
                        code,
                        elapsed_ms,
                        wait,
                    )
                    time.sleep(wait)
                    last_exc = exc
                    continue

                # ── Non-retryable error — raise immediately ──────────────────
                logger.error(
                    "event=db_error attempt=%s code=%s elapsed_ms=%s error=%s",
                    attempt,
                    code,
                    elapsed_ms,
                    exc,
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

        return self._execute_with_retry(_op, sql_query, params, readonly=is_select)

    def fetch_query(self, sql_query: str, params: Any = None) -> list[dict[str, Any]]:
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
                    converted = sql
                    named_batch = batch

                result = conn.execute(text(converted), named_batch)
                total += result.rowcount
            return total

        return self._execute_with_retry(_op, sql_query, params_list)

    def fetch_query_safe(self, sql_query: str, params: Any = None) -> list[dict]:
        """Execute a SELECT; return [] on any error instead of raising."""
        try:
            return self.fetch_query(sql_query, params)
        except SQLAlchemyError as e:
            logger.error("event=db_fetch_safe_failed sql=%s error=%s", sql_query, e)
            return []

    def execute_query_safe(self, sql_query: str, params: Any = None) -> list | int:
        """Execute a statement; return [] or 0 on any error instead of raising."""
        try:
            return self.execute_query(sql_query, params)
        except SQLAlchemyError as e:
            logger.error("event=db_execute_safe_failed sql=%s error=%s", sql_query, e)
            return [] if sql_query.strip().upper().startswith("SELECT") else 0

    def close(self) -> None:
        """No-op — connection lifecycle is managed by the pool."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.close()
