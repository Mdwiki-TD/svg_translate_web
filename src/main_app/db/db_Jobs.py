"""Database module for managing background jobs."""

from __future__ import annotations

# import json
import logging
from datetime import datetime
from typing import Any, List

from ..config import DbConfig
from .engine import Database
from .models import JobRecord

logger = logging.getLogger(__name__)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        logger.exception("Failed to parse datetime: %s", value)
        return None


class JobsDB:
    """MySQL-backed job store."""

    def __init__(self, database_data: DbConfig | None = None, db: Database | None = None):
        """
        Initialize the JobsDB with the provided database configuration and ensure the jobs table exists.

        Parameters:
            database_data (DbConfig): Configuration used to instantiate the Database wrapper (connection details, credentials, and options).
        """
        self.db = db or Database(database_data)

    def _row_to_record(self, row: dict[str, Any]) -> JobRecord:
        return JobRecord(
            id=int(row["id"]),
            job_type=row["job_type"],
            username=row.get("username"),
            status=row["status"],
            started_at=_parse_dt(row.get("started_at")),
            completed_at=_parse_dt(row.get("completed_at")),
            result_file=row.get("result_file"),
            created_at=_parse_dt(row.get("created_at")),
            updated_at=_parse_dt(row.get("updated_at")),
        )

    def create(self, job_type: str, username: str | None = None) -> JobRecord:
        """Create a new job."""
        job_id = self.db.insert_query(
            """
            INSERT INTO jobs (job_type, status, username) VALUES (%s, %s, %s)
            """,
            (job_type, "pending", username),
        )
        rows = self.db.fetch_query_safe(
            """
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE id = %s
            """,
            (job_id,),
        )
        if not rows:
            logger.exception("Failed to create job")
            raise RuntimeError("Failed to create job")
        return self._row_to_record(rows[0])

    def delete(self, job_id: int, job_type: str = "fix_nested_main_files") -> bool:
        query = """
            DELETE FROM jobs
            WHERE id = %s AND job_type = %s
        """
        try:
            self.db.execute_query_safe(
                query,
                (job_id, job_type),
            )
            return True
        except Exception as e:
            logger.exception(f"Failed to delete job id {job_id} of type {job_type}: {e}")
            return False

    def get(self, job_id: int, job_type: str = "fix_nested_main_files") -> JobRecord:
        """Get a job by ID."""
        rows = self.db.fetch_query_safe(
            """
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE id = %s AND job_type = %s
            """,
            (job_id, job_type),
        )
        if not rows:
            logger.exception("Failed to get job")
            raise LookupError(f"Job id {job_id} was not found")
        return self._row_to_record(rows[0])

    def list(self, limit: int = 100, job_type: str | None = None) -> List[JobRecord]:
        """List recent jobs, optionally filtered by job_type."""
        if job_type:
            rows = self.db.fetch_query_safe(
                """
                SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
                FROM jobs
                WHERE job_type = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (job_type, limit),
            )
        else:
            rows = self.db.fetch_query_safe(
                """
                SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
        return [self._row_to_record(row) for row in rows]

    def update_running_status(
        self,
        job_id: int,
        job_type: str = "fix_nested_main_files",
        result_file: str | None = None,
    ) -> JobRecord:
        """
        Update job status.
        Raises LookupError if the job doesn't exist or the update fails.
        """
        query = "UPDATE jobs SET status = 'running', started_at = NOW()"
        params = []
        if result_file is not None:
            query += ", result_file = %s"
            params.append(result_file)

        query += " WHERE id = %s AND job_type = %s"
        params.append(job_id)
        params.append(job_type)

        rowcount = self.db.execute_query_safe(query, tuple(params))
        if rowcount == 0:
            logger.exception(f"Failed to update job id {job_id} to running status")
            raise LookupError(f"Job id {job_id} was not found or update failed")

        return self.get(job_id, job_type)

    def update_status(
        self,
        job_id: int,
        status: str,
        result_file: str | None = None,
        job_type: str = "fix_nested_main_files",
    ) -> JobRecord:
        """
        Update job status.
        Raises LookupError if the job doesn't exist or the update fails.
        """
        if status == "running":
            return self.update_running_status(job_id, job_type, result_file)

        if status in ["completed", "failed", "cancelled"]:
            rowcount = self.db.execute_query_safe(
                """
                UPDATE jobs
                SET status = %s, completed_at = NOW(), result_file = %s
                WHERE id = %s AND job_type = %s
                """,
                (status, result_file, job_id, job_type),
            )
        else:
            rowcount = self.db.execute_query_safe(
                """
                UPDATE jobs
                SET status = %s
                WHERE id = %s AND job_type = %s
                """,
                (status, job_id, job_type),
            )

        if rowcount == 0:
            logger.exception(f"Failed to update job id {job_id} to status {status}")
            raise LookupError(f"Job id {job_id} was not found or update failed")

        return self.get(job_id, job_type)

    def cancel(self, job_id: int, job_type: str | None = None) -> bool:
        """
        Mark a job as cancelled in the database.
        Returns True if the job was found and its status was updated to 'cancelled'.
        """
        query = "UPDATE jobs SET status = 'cancelled', completed_at = NOW() WHERE id = %s AND status IN ('pending', 'running')"
        params = [job_id]
        if job_type:
            query += " AND job_type = %s"
            params.append(job_type)

        rowcount = self.db.execute_query_safe(query, tuple(params))
        return rowcount > 0

    def is_cancelled(self, job_id: int, job_type: str) -> bool:
        """
        Check if a job is marked as cancelled in the database.
        """
        rows = self.db.fetch_query_safe(
            "SELECT status FROM jobs WHERE id = %s AND job_type = %s",
            (job_id, job_type),
        )
        if not rows:
            return False
        return rows[0]["status"] == "cancelled"


__all__ = [
    "JobsDB",
    "JobRecord",
]
