from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import json

from ..config import DbConfig
from . import Database

logger = logging.getLogger(__name__)


class SettingsDB:
    """MySQL-backed application settings store."""

    def __init__(self, database_data: DbConfig, use_bg_engine: bool = False):
        self.db = Database(database_data, use_bg_engine=use_bg_engine)
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.db.execute_query_safe(
            """
            CREATE TABLE IF NOT EXISTS `settings` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `key` VARCHAR(190) COLLATE utf8mb4_unicode_ci NOT NULL,
                `title` VARCHAR(500) COLLATE utf8mb4_unicode_ci NOT NULL,
                `value` TEXT COLLATE utf8mb4_unicode_ci NULL,
                `value_type` ENUM('boolean','string','integer','json')
                    COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'boolean',
                PRIMARY KEY (`id`),
                UNIQUE KEY `unique_key` (`key`)
            ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci;
            """
        )

    def get_all(self) -> Dict[str, Any]:
        """Fetch all settings and return them as a dictionary of key -> parsed value."""
        rows = self.db.fetch_query_safe("SELECT `key`, `value`, `value_type` FROM `settings`")
        settings_dict = {}
        for row in rows:
            settings_dict[row["key"]] = self._parse_value(row["value"], row["value_type"])
        return settings_dict

    def get_raw_all(self) -> List[Dict[str, Any]]:
        """Fetch all settings as raw rows for admin panel."""
        return self.db.fetch_query_safe("SELECT * FROM `settings` ORDER BY `id` ASC")

    def get_by_key(self, key: str) -> Optional[Any]:
        rows = self.db.fetch_query_safe(
            "SELECT `value`, `value_type` FROM `settings` WHERE `key` = %s",
            (key,)
        )
        if not rows:
            return None
        return self._parse_value(rows[0]["value"], rows[0]["value_type"])

    def create_setting(self, key: str, title: str, value_type: str, value: Any) -> bool:
        """Create a new setting."""
        str_val = self._serialize_value(value, value_type)
        if self.get_by_key(key) is not None:
            return False
        try:
            affected_rows = self.db.execute_query_safe(
                # "INSERT IGNORE INTO `settings` (`key`, `title`, `value_type`, `value`) VALUES (%s, %s, %s, %s)",
                "INSERT INTO `settings` (`key`, `title`, `value_type`, `value`) VALUES (%s, %s, %s, %s)",
                (key, title, value_type, str_val)
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to create setting '{key}': {e}")
            return False

    def update_setting(self, key: str, value: Any, value_type: str | None = None) -> bool:
        """Update an existing setting.

        Args:
            key: The setting key to update.
            value: The new value.
            value_type: Optional value type. If provided, skips the SELECT query.
        """
        # If value_type not provided, retrieve it from the database
        if value_type is None:
            rows = self.db.fetch_query_safe("SELECT `value_type` FROM `settings` WHERE `key` = %s", (key,))
            if not rows:
                return False
            value_type = rows[0]["value_type"]

        str_val = self._serialize_value(value, value_type)

        try:
            self.db.execute_query_safe(
                "UPDATE `settings` SET `value` = %s WHERE `key` = %s",
                (str_val, key)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update setting '{key}': {e}")
            return False

    def _parse_value(self, value: Optional[str], value_type: str) -> Any:
        if value is None:
            return None
        if value_type == "boolean":
            return value.lower() in ("1", "true", "yes", "on")
        elif value_type == "integer":
            try:
                return int(value)
            except ValueError:
                return 0
        elif value_type == "json":
            try:
                return json.loads(value)
            except Exception:
                return None
        return value  # string

    def _serialize_value(self, value: Any, value_type: str) -> Optional[str]:
        if value is None:
            return None
        if value_type == "boolean":
            return "true" if value else "false"
        elif value_type == "integer":
            try:
                return str(int(value))
            except (ValueError, TypeError):
                return "0"
        elif value_type == "json":
            return json.dumps(value, ensure_ascii=False)
        return str(value)
