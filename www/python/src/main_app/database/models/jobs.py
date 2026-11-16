from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    FetchedValue,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import Model

logger = logging.getLogger(__name__)


class JobRecord(Model):
    """
    CREATE TABLE `jobs` (
        `id` int NOT NULL AUTO_INCREMENT,
        `job_type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
        `username` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
        `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
        `started_at` datetime DEFAULT NULL,
        `completed_at` datetime DEFAULT NULL,
        `result_file` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        `is_running` tinyint(1) DEFAULT NULL,
        `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`),
        UNIQUE KEY `idx_unique_active_job` (`job_type`,`is_running`),
        KEY `status_username` (`status`,`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    Notes:
        username has no FK — jobs persist independently of user accounts.

        ``is_running`` is 1 while the job holds the lock and NULL otherwise.
        Never store 0: the UNIQUE (job_type, is_running) key allows only one
        row per job_type for any non-NULL value, while NULLs never conflict.
    """

    __tablename__ = "jobs"

    __table_args__ = (
        # One running job per job_type; NULL values never conflict
        UniqueConstraint("job_type", "is_running", name="idx_unique_active_job"),
        # Composite index for status + username ordering
        Index("status_username", "status", "username"),
        # Optional: forbids 0 so the unique lock can't be broken by mistake
        CheckConstraint(
            "is_running IS NULL OR is_running = 1",
            name="chk_jobs_is_running_null_or_one",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default="pending",
    )
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)
    result_file: Mapped[str | None] = mapped_column(String(500), default=None)

    # 1 = running (holds the lock), NULL = not running. Never store 0.
    is_running: Mapped[bool | None] = mapped_column(default=None)
    # is_running: Mapped[int | None] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
        server_onupdate=FetchedValue(),  # MySQL handles ON UPDATE CURRENT_TIMESTAMP
    )


__all__ = [
    "JobRecord",
]
