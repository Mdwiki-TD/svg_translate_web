from __future__ import annotations

import logging

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from ..engine import LONGTEXT, BaseDb

logger = logging.getLogger(__name__)


class FixNestedTaskRecord(BaseDb):
    """
    CREATE TABLE `fix_nested_tasks` (
      `id` varchar(128) NOT NULL,
      `username` text DEFAULT NULL,
      `filename` text NOT NULL,
      `status` varchar(64) NOT NULL,
      `nested_tags_before` int(11) DEFAULT NULL,
      `nested_tags_after` int(11) DEFAULT NULL,
      `nested_tags_fixed` int(11) DEFAULT NULL,
      `download_result` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`download_result`)),
      `upload_result` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`upload_result`)),
      `error_message` text DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `idx_fix_nested_status` (`status`),
      KEY `idx_fix_nested_username` (`username`(255)),
      KEY `idx_fix_nested_created` (`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "fix_nested_tasks"

    id = Column(String(128), primary_key=True)
    username = Column(Text, nullable=True)
    filename = Column(Text, nullable=False)
    status = Column(String(64), nullable=False)
    nested_tags_before = Column(Integer, nullable=True)
    nested_tags_after = Column(Integer, nullable=True)
    nested_tags_fixed = Column(Integer, nullable=True)

    download_result = Column(LONGTEXT, nullable=True)
    upload_result = Column(LONGTEXT, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


__all__ = [
    "FixNestedTaskRecord",
]
