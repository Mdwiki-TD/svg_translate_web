from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
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

    id: int
    job_type: str
    username: str | None = None  # User who started the job
    status: str  # pending, running, completed, failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_file: str | None = None  # Path to JSON file with job results
    created_at: datetime | None = None
    updated_at: datetime | None = None


__all__ = [
    "JobRecord",
]
