from __future__ import annotations

import logging

from sqlalchemy import Column, DateTime, Index, Integer, String, UniqueConstraint, func

from ...extensions import db

logger = logging.getLogger(__name__)


class JobRecord(db.Model):
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

    NOTE: username has no FK — jobs persist independently of user accounts.
    """

    __tablename__ = "jobs"
    __table_args__ = (
        # Unique constraint combining job_type and is_running
        UniqueConstraint("job_type", "is_running", name="idx_unique_active_job"),
        # Keep the standard index for username if needed
        Index("username", "username"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, server_default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result_file = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
    is_running = Column(Integer, nullable=True)


__all__ = [
    "JobRecord",
]
