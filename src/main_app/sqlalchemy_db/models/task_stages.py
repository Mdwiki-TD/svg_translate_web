from __future__ import annotations

import logging

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func

from ..engine import LONGTEXT, BaseDb

logger = logging.getLogger(__name__)


class TaskStageRecord(BaseDb):
    """
    CREATE TABLE `task_stages` (
      `stage_id` varchar(255) NOT NULL,
      `task_id` varchar(128) NOT NULL,
      `stage_name` varchar(255) NOT NULL,
      `stage_number` int(11) NOT NULL,
      `stage_status` varchar(64) NOT NULL,
      `stage_sub_name` longtext DEFAULT NULL,
      `stage_message` longtext DEFAULT NULL,
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`stage_id`),
      UNIQUE KEY `uq_task_stage` (`task_id`,`stage_name`),
      KEY `idx_task_stages_task` (`task_id`,`stage_number`),
      CONSTRAINT `fk_task_stage_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "task_stages"

    stage_id = Column(String(255), primary_key=True)
    task_id = Column(String(128), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    stage_name = Column(String(255), nullable=False)
    stage_number = Column(Integer, nullable=False)
    stage_status = Column(String(64), nullable=False)
    stage_sub_name = Column(LONGTEXT, nullable=True)
    stage_message = Column(LONGTEXT, nullable=True)

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )

    __table_args__ = (UniqueConstraint("task_id", "stage_name", name="uq_task_stage"),)


__all__ = [
    "TaskStageRecord",
]
