from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from ..config import DbConfig
from .engine import Database
from .models import SettingRecord

logger = logging.getLogger(__name__)


class SettingsDB:
    """MySQL-backed application settings store."""

    def __init__(self, database_data: DbConfig | None = None, db: Database | None = None):
        self.db = db or Database(database_data)

    def _row_to_record(self, row: dict[str, Any]) -> SettingRecord:
        value = self._parse_value(row["value"], row["value_type"])
        if not row.get("id"):
            raise ValueError(f"Missing id field in settings row for key '{row.get('key', 'unknown')}'")

        return SettingRecord(
            id=int(row["id"]),
            key=row["key"],
            title=row.get("title"),
            value_type=row["value_type"],
            value=value,
        )

    def all(self) -> list[SettingRecord]:
        """Fetch all settings and return them as a dictionary of key -> parsed value."""
        rows = self.db.fetch_query_safe("SELECT id, key, title, value_type, value FROM settings")
        return [self._row_to_record(row) for row in rows]

    def _is_key_exist(self, key: str) -> None | SettingRecord:
        rows = self.db.fetch_query_safe(
            "SELECT id, key, title, value_type, value FROM settings WHERE key = %s",
            (key,),
        )
        if not rows:
            return None
        return True

    def get_by_key(self, key: str) -> None | SettingRecord:
        rows = self.db.fetch_query_safe("SELECT id, key, title, value_type, value FROM settings WHERE key = %s", (key,))
        if not rows:
            return None
        return self._row_to_record(rows[0])

    def get_all(self) -> Dict[str, Any]:
        """Fetch all settings and return them as a dictionary of key -> parsed value."""
        rows = self.db.fetch_query_safe("SELECT id, key, title, value_type, value FROM settings")
        settings_dict = {}
        for row in rows:
            settings_dict[row["key"]] = self._parse_value(row["value"], row["value_type"])
        return settings_dict

    def get_raw_all(self) -> List[Dict[str, Any]]:
        """Fetch all settings as raw rows for admin panel."""
        return self.db.fetch_query_safe("SELECT id, key, title, value_type, value FROM settings ORDER BY id ASC")

    def create(self, key: str, title: str, value_type: str, value: Any) -> bool:
        """Create a new setting."""
        if self._is_key_exist(key) is True:
            return False
        try:
            affected_rows = self.db.insert_query(
                "INSERT INTO settings (key, title, value_type, value) VALUES (%s, %s, %s, %s)",
                (key, title, value_type, value),
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to create setting '{key}': {e}")
            return False

    def update(
        self,
        key: str,
        value: Any,
        title: str | None = None,
    ) -> bool:
        """Update an existing setting.

        Args:
            key: The setting key to update.
            value: The new value.
        """
        if not self._is_key_exist(key):
            return False

        query = "UPDATE settings SET value = %s WHERE key = %s"
        params = (value, key)

        if title:
            query = "UPDATE settings SET value = %s, title = %s WHERE key = %s"
            params = (value, title, key)

        try:
            self.db.execute_query_safe(query, params)
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

    def delete(self, key: str) -> bool:
        """Delete a setting by key."""
        try:
            affected_rows = self.db.execute_query_safe("DELETE FROM settings WHERE key = %s", (key,))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to delete setting '{key}': {e}")
            return False
