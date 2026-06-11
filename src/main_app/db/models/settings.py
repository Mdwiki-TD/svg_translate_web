from __future__ import annotations

import logging

from sqlalchemy import Column, Enum, Integer, String, Text

from ...extensions import db

logger = logging.getLogger(__name__)


class SettingRecord(db.Model):
    """
    CREATE TABLE `settings` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `key` varchar(190) NOT NULL,
      `title` varchar(500) NOT NULL,
      `value` text DEFAULT NULL,
      `value_type` enum('boolean','string','integer') NOT NULL DEFAULT 'boolean',
      PRIMARY KEY (`id`),
      UNIQUE KEY `unique_key` (`key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(190), unique=True, nullable=False)
    title = Column(String(500), nullable=False)

    value_type = Column(Enum("boolean", "string", "integer"), nullable=False, server_default="boolean")

    value = Column(Text, nullable=True)


__all__ = [
    "SettingRecord",
]
