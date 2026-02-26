from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable, List

import pymysql

from ..config import DbConfig
from .db_class import Database
from .db_sqlalchemy import DatabaseSQLAlchemy
from .engine_factory import USE_SQLALCHEMY_POOLING

logger = logging.getLogger(__name__)


@dataclass
class CoordinatorRecord:
    """Representation of a coordinator/admin account."""

    id: int
    username: str
    is_active: bool
    created_at: Any | None = None
    updated_at: Any | None = None


class CoordinatorsDB:
    """MySQL-backed coordinator persistence using the shared Database helper."""

    def __init__(
        self,
        database_data: DbConfig,
        use_background_engine: bool = False,
    ):
        """
        Initialize CoordinatorsDB with the provided database configuration.

        Args:
            database_data: Database connection configuration
            use_background_engine: Use background-optimized engine for batch processing
        """
        if USE_SQLALCHEMY_POOLING:
            self.db = DatabaseSQLAlchemy(
                database_data,
                use_background_engine=use_background_engine,
            )
            logger.debug(
                "event=coordinators_db_init engine=sqlalchemy background=%s",
                use_background_engine,
            )
        else:
            self.db = Database(database_data)
            logger.debug("event=coordinators_db_init engine=pymysql")

        self._ensure_table()

    def _ensure_table(self) -> None:
        """
        Ensure the required `admin_users` table exists in the database with the expected schema.

        Creates the `admin_users` table if it does not already exist with columns:
        - `id` (INT, auto-increment primary key)
        - `username` (VARCHAR(255), unique, not null)
        - `is_active` (TINYINT(1), not null, default 1)
        - `created_at` (TIMESTAMP, defaults to current timestamp)
        - `updated_at` (TIMESTAMP, defaults to current timestamp and updates on row change)

        The table uses the InnoDB engine and `utf8mb4` character set.
        """
        self.db.execute_query_safe(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    def _row_to_record(self, row: dict[str, Any]) -> CoordinatorRecord:
        return CoordinatorRecord(
            id=int(row["id"]),
            username=row["username"],
            is_active=bool(row.get("is_active")),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _fetch_by_id(self, coordinator_id: int) -> CoordinatorRecord:
        rows = self.db.fetch_query_safe(
            """
            SELECT id, username, is_active, created_at, updated_at
            FROM admin_users
            WHERE id = %s
            """,
            (coordinator_id,),
        )
        if not rows:
            raise LookupError(f"Coordinator id {coordinator_id} was not found")
        return self._row_to_record(rows[0])

    def _fetch_by_username(self, username: str) -> CoordinatorRecord:
        rows = self.db.fetch_query_safe(
            """
            SELECT id, username, is_active, created_at, updated_at
            FROM admin_users
            WHERE username = %s
            """,
            (username,),
        )
        if not rows:
            raise LookupError(f"Coordinator {username!r} was not found")
        return self._row_to_record(rows[0])

    def seed(self, usernames: Iterable[str]) -> None:
        clean_usernames = [name.strip() for name in usernames if name and name.strip()]
        if not clean_usernames:
            return

        placeholders = ", ".join(["%s"] * len(clean_usernames))
        existing_rows = self.db.fetch_query_safe(
            f"SELECT username FROM admin_users WHERE username IN ({placeholders})",
            tuple(clean_usernames),
        )
        existing = {row["username"] for row in existing_rows}
        for username in clean_usernames:
            if username in existing:
                continue
            self.db.execute_query_safe(
                "INSERT INTO admin_users (username, is_active) VALUES (%s, 1)",
                (username,),
            )

    def list(self) -> List[CoordinatorRecord]:
        rows = self.db.fetch_query_safe(
            """
            SELECT id, username, is_active, created_at, updated_at
            FROM admin_users
            ORDER BY id ASC
            """
        )
        return [self._row_to_record(row) for row in rows]

    def add(self, username: str) -> CoordinatorRecord:
        username = username.strip()
        if not username:
            raise ValueError("Username is required")

        try:
            # Use execute_query to allow exception to propagate
            self.db.execute_query(
                "INSERT INTO admin_users (username, is_active) VALUES (%s, 1)",
                (username,),
            )
        except pymysql.err.IntegrityError:
            # This assumes a UNIQUE constraint on the username column
            raise ValueError(f"Coordinator '{username}' already exists") from None

        return self._fetch_by_username(username)

    def set_active(self, coordinator_id: int, is_active: bool) -> CoordinatorRecord:
        _ = self._fetch_by_id(coordinator_id)
        self.db.execute_query_safe(
            "UPDATE admin_users SET is_active = %s WHERE id = %s",
            (1 if is_active else 0, coordinator_id),
        )
        return self._fetch_by_id(coordinator_id)

    def delete(self, coordinator_id: int) -> CoordinatorRecord:
        record = self._fetch_by_id(coordinator_id)
        self.db.execute_query_safe(
            "DELETE FROM admin_users WHERE id = %s",
            (coordinator_id,),
        )
        return record


__all__ = [
    "CoordinatorRecord",
    "CoordinatorsDB",
]
