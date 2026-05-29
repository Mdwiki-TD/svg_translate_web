from __future__ import annotations

import logging

from sqlalchemy import Column, DateTime, Integer, String, func, text

from ...extensions import db

logger = logging.getLogger(__name__)


class JobRecord(db.Model):
    """
    CREATE TABLE `jobs` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `job_type` varchar(255) NOT NULL,
      `username` varchar(255) DEFAULT NULL,
      `status` varchar(50) NOT NULL DEFAULT 'pending',
      `started_at` timestamp NULL DEFAULT NULL,
      `completed_at` timestamp NULL DEFAULT NULL,
      `result_file` varchar(500) DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `idx_status_created` (`status`,`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
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


__all__ = [
    "JobRecord",
]
