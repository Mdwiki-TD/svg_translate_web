from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SettingRecord:
    """
    CREATE TABLE `settings` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `key` varchar(190) NOT NULL,
      `title` varchar(500) NOT NULL,
      `value` text DEFAULT NULL,
      `value_type` enum('boolean','string','integer','json') NOT NULL DEFAULT 'boolean',
      PRIMARY KEY (`id`),
      UNIQUE KEY `unique_key` (`key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    __tablename__ = "settings"

    id: int
    key: str
    title: str
    value_type: str = "boolean"
    value: str | None = None

    def __post_init__(self):
        value_types = ["boolean", "string", "integer", "json"]
        if self.value_type not in value_types:
            raise ValueError(f"Invalid value_type: {self.value_type}. Must be one of {value_types}")

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'key': self.key,
            'title': self.title,
            'value_type': self.value_type,
            'value': self.value,
        }


__all__ = [
    "SettingRecord",
]
