from __future__ import annotations

import logging

from enum import StrEnum
from sqlalchemy import String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db

logger = logging.getLogger(__name__)

class ValueType(StrEnum):
    BOOLEAN = "boolean"
    STRING = "string"
    INTEGER = "integer"


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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(190), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    value_type: Mapped[ValueType] = mapped_column(
        nullable=False,
        server_default=text("'boolean'")
    )

    value: Mapped[str | None] = mapped_column(Text, nullable=True)



__all__ = [
    "SettingRecord",
]
