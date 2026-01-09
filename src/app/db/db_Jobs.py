"""Database module for managing background jobs."""

from __future__ import annotations

# import json
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Any, List

from . import Database

logger = logging.getLogger("svg_translate")


@dataclass
class JobRecord:
    """Representation of a background job."""

    id: int
    job_type: str
    status: str  # pending, running, completed, failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_file: str | None = None  # Path to JSON file with job results
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JobsDB:
    """MySQL-backed job store."""

    def __init__(self, db_data: dict[str, Any]):
        self.db = Database(db_data)
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.db.execute_query_safe(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_type VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                result_file VARCHAR(500) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_status_created (status, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    def _row_to_record(self, row: dict[str, Any]) -> JobRecord:
        return JobRecord(
            id=int(row["id"]),
            job_type=row["job_type"],
            status=row["status"],
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            result_file=row.get("result_file"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def create(self, job_type: str) -> JobRecord:
        """Create a new job."""
        self.db.execute_query_safe(
            """
            INSERT INTO jobs (job_type, status) VALUES (%s, %s)
            """,
            (job_type, "pending"),
        )
        rows = self.db.fetch_query_safe(
            """
            SELECT id, job_type, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE id = LAST_INSERT_ID()
            """
        )
        if not rows:
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
            SELECT id, job_type, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE id = %s AND job_type = %s
            """,
            (job_id, job_type),
        )
        if not rows:
            raise LookupError(f"Job id {job_id} was not found")
        return self._row_to_record(rows[0])

    def list(self, limit: int = 100) -> List[JobRecord]:
        """List recent jobs."""
        rows = self.db.fetch_query_safe(
            """
            SELECT id, job_type, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [self._row_to_record(row) for row in rows]

    def update_status(
        self, job_id: int, status: str, result_file: str | None = None, job_type: str = "fix_nested_main_files"
    ) -> JobRecord:
        """
        Update job status.
        TODO: Using execute_query_safe means UPDATE failures are logged but don't raise exceptions. If an update fails (e.g., job_id doesn't exist), the method proceeds to call get(job_id) which will raise LookupError. However, if the job exists but the UPDATE fails for other reasons (connection issues), the returned record won't reflect the intended status change, with no indication to the caller. Consider using execute_query instead and letting exceptions propagate, or checking the rowcount to verify the update succeeded.
        """
        if status == "running":
            if result_file is not None:
                self.db.execute_query_safe(
                    """
                    UPDATE jobs
                    SET status = %s, started_at = NOW(), result_file = %s
                    WHERE id = %s AND job_type = %s
                    """,
                    (status, result_file, job_id, job_type),
                )
            else:
                self.db.execute_query_safe(
                    """
                    UPDATE jobs
                    SET status = %s, started_at = NOW()
                    WHERE id = %s AND job_type = %s
                    """,
                    (status, job_id, job_type),
                )
            return self.get(job_id)

        if status in ["completed", "failed"]:
            self.db.execute_query_safe(
                """
                UPDATE jobs
                SET status = %s, completed_at = NOW(), result_file = %s
                WHERE id = %s AND job_type = %s
                """,
                (status, result_file, job_id, job_type),
            )
        else:
            self.db.execute_query_safe(
                """
                UPDATE jobs
                SET status = %s
                WHERE id = %s AND job_type = %s
                """,
                (status, job_id, job_type),
            )
        return self.get(job_id, job_type)


__all__ = [
    "JobsDB",
    "JobRecord",
]
