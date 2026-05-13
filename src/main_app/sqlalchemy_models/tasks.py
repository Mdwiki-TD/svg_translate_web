from __future__ import annotations

import logging

from sqlalchemy import Column, DateTime, String, Text, func

from ..shared.engine import BaseDb, LONGTEXT

logger = logging.getLogger(__name__)


class TaskRecord(BaseDb):
    """
    CREATE TABLE `tasks` (
      `id` varchar(128) NOT NULL,
      `username` text DEFAULT NULL,
      `title` text NOT NULL,
      `normalized_title` varchar(512) NOT NULL,
      `main_file` varchar(512) DEFAULT NULL,
      `status` varchar(64) NOT NULL,
      `form_json` longtext DEFAULT NULL,
      `data_json` longtext DEFAULT NULL,
      `results_json` longtext DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `idx_tasks_norm` (`normalized_title`),
      KEY `idx_tasks_status` (`status`),
      KEY `idx_tasks_created` (`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "tasks"

    id = Column(String(128), primary_key=True)
    username = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    normalized_title = Column(String(512), nullable=False)
    main_file = Column(String(512), nullable=True)
    status = Column(String(64), nullable=False)

    form_json = Column(LONGTEXT, nullable=True)
    data_json = Column(LONGTEXT, nullable=True)
    results_json = Column(LONGTEXT, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


__all__ = [
    "TaskRecord",
]
