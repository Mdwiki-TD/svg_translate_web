from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import Index, String, UniqueConstraint, text
from sqlalchemy import DateTime, FetchedValue, func
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import Model

logger = logging.getLogger(__name__)


class JobRecord(Model):
    """
    CREATE TABLE `jobs` (
        `id` int NOT NULL AUTO_INCREMENT,
        `job_type` varchar(255) NOT NULL,
        `username` varchar(255) NOT NULL,
        `status` varchar(50) NOT NULL DEFAULT 'pending',
        `started_at` datetime DEFAULT NULL,
        `completed_at` datetime DEFAULT NULL,
        `result_file` varchar(500) DEFAULT NULL,
        `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `is_running` tinyint DEFAULT NULL,
        PRIMARY KEY (`id`),
        UNIQUE KEY `idx_unique_active_job` (`job_type`,`is_running`),
        KEY `username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    NOTE: username has no FK — jobs persist independently of user accounts.
    """

    __tablename__ = "jobs"

    __table_args__ = (
        # Unique constraint combining job_type and is_running
        UniqueConstraint("job_type", "is_running", name="idx_unique_active_job"),
        # Composite index for status + username ordering
        Index("status_username", "status", "username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'pending'"))

    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    result_file: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_running: Mapped[int | None] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        default=func.current_timestamp(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        default=func.current_timestamp(),
        server_onupdate=FetchedValue(),  # MySQL handles ON UPDATE CURRENT_TIMESTAMP
        onupdate=func.current_timestamp(),
    )


__all__ = [
    "JobRecord",
]
