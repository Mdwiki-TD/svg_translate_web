from __future__ import annotations

import logging
import re
import sqlite3
import threading
from typing import Any, Iterable, Sequence

from ..config import DbConfig

logger = logging.getLogger(__name__)


def _mysql_to_sqlite(sql: str) -> str:
    """Convert %s placeholders to ? for SQLite."""
    return re.sub(r"%s", "?", sql)


class DatabaseSqlLite:
    """SQLite drop-in replacement for DatabaseSqlLite — for testing only."""

    def __init__(
        self,
        database_data: DbConfig | None = None,
        # db_path: str = "./memory.sqlite3",
        db_path: str = ":memory:",
    ):
        self._lock = threading.RLock()
        self.connection = None
        self.db_path = db_path

    def _init_connection(self):
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # as DictCursor
        self.connection.isolation_level = None  # autocommit mode

    def close(self):
        with self._lock:
            if self.connection:
                self.connection.close()
                self.connection = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _dict_rows(self, cursor) -> list[dict]:
        rows = cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    def _execute_many_batch(self, cursor, sql: str, batch: Sequence[Any]) -> int:
        """Mirror the recursive batch-splitting logic from Database."""
        if not batch:
            return 0
        try:
            cursor.executemany(sql, batch)
            return cursor.rowcount
        except sqlite3.OperationalError:
            if len(batch) <= 1:
                raise
            mid = (len(batch) + 1) // 2
            return self._execute_many_batch(cursor, sql, batch[:mid]) + self._execute_many_batch(
                cursor, sql, batch[mid:]
            )

    # ------------------------------------------------------------------
    # Public API  (same as Database)
    # ------------------------------------------------------------------
    def execute_query(self, sql_query: str, params: Any = None, **kwargs):
        sql = _mysql_to_sqlite(sql_query)
        if not self.connection:
            self._init_connection()
        with self._lock:
            cur = self.connection.cursor()
            cur.execute(sql, params or [])
            if cur.description:
                return self._dict_rows(cur)
            return cur.rowcount

    def fetch_query(self, sql_query: str, params: Any = None, **kwargs) -> list[dict]:
        sql = _mysql_to_sqlite(sql_query)
        if not self.connection:
            self._init_connection()
        with self._lock:
            cur = self.connection.cursor()
            cur.execute(sql, params or [])
            return self._dict_rows(cur)

    def insert_query(
        self,
        sql_query: str,
        params: Any = None,
        **kwargs,
    ) -> int:
        """Execute an INSERT and return the lastrowid."""
        sql = _mysql_to_sqlite(sql_query)
        if not self.connection:
            self._init_connection()
        with self._lock:
            cur = self.connection.cursor()
            cur.execute(sql, params or [])
            return cur.lastrowid

    def execute_many(
        self,
        sql_query: str,
        params_seq: Iterable[Any],
        batch_size: int = 1000,
        **kwargs,
    ) -> int:
        params_list = list(params_seq)
        if not params_list:
            return 0
        sql = _mysql_to_sqlite(sql_query)
        if not self.connection:
            self._init_connection()
        with self._lock:
            cur = self.connection.cursor()
            total = 0
            for i in range(0, len(params_list), batch_size):
                batch = params_list[i : i + batch_size]
                total += self._execute_many_batch(cur, sql, batch)
        return total

    def fetch_query_safe(self, sql_query, params=None, **kwargs) -> list[dict]:
        try:
            return self.fetch_query(sql_query, params)
        except sqlite3.Error:
            return []

    def execute_query_safe(self, sql_query, params=None, **kwargs):
        try:
            return self.execute_query(sql_query, params)
        except sqlite3.Error:
            if sql_query.strip().lower().startswith("select"):
                return []
            return 0
