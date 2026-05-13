from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SettingRecord:
    """
    """
    # `id` INT NOT NULL AUTO_INCREMENT,
    # `key` VARCHAR(190) NOT NULL,
    # `title` VARCHAR(500) NOT NULL,
    # `value_type` enum ('boolean', 'string', 'integer', 'json') NOT NULL DEFAULT 'boolean',
    # `value` text DEFAULT NULL,
    id: int
    key: str
    title: str
    value_type: str
    value: str | None = None

    def __post_init__(self):
        ...

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'key': self.key,
            'title': self.title,
            'value_type': self.value_type,
            'value': self.value,
        }
