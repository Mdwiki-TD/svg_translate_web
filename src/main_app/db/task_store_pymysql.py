from __future__ import annotations

import logging

from ..config import DbConfig
from ..db.sql_shema_tables import sql_tables
from .db_class import Database
from .db_CreateUpdate import CreateUpdateTask
from .db_StageStore import StageStore
from .db_TasksListDB import TasksListDB
from .utils import DbUtils

logger = logging.getLogger(__name__)


class TaskStorePyMysql(CreateUpdateTask, StageStore, TasksListDB, DbUtils):
    """MySQL-backed task store using helper functions execute_query/fetch_query."""

    def __init__(self, database_data: DbConfig) -> None:
        # Note: db connection is managed inside execute_query/fetch_query
        # self._lock = threading.Lock()
        """
        Initialize the task store with the given database configuration and ensure required schema and indexes exist.

        Parameters:
            database_data (DbConfig): Database connection configuration used to create the internal Database instance.
        """
        self.db = Database(database_data)
        self._init_schema()
        super().__init__(self.db)

    def close(self) -> None:
        """Close the underlying database connection."""
        self.db.close()

    def __enter__(self) -> TaskStorePyMysql:
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    def _init_schema(self) -> None:
        """
        Ensure the tasks table and its indexes exist in the MySQL database.

        Creates the tasks table (with text-based JSON columns for broad MySQL compatibility) and
        ensures indexes on normalized_title, status, and created_at are present. Index creation is
        guarded for compatibility with MySQL versions that do not support CREATE INDEX IF NOT EXISTS.
        Logs a warning if schema initialization fails.
        """
        # ---
        self.db.execute_query_safe(sql_tables.tasks)
        self.db.execute_query_safe(sql_tables.task_stages)
