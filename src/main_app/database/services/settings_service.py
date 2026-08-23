"""
SQLAlchemy-based service for managing settings.
"""

from __future__ import annotations

import logging
from typing import Any

from ...extensions import db
from ..models import SettingRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


def _serialize_value(value: Any, value_type: str) -> str | None:
    if value is None:
        return None
    if value_type == "boolean":
        return "true" if value else "false"
    elif value_type == "integer":
        try:
            return str(int(value))
        except (ValueError, TypeError):
            return "0"
    return str(value)


def format_values(records: list[SettingRecord]) -> dict[str, Any]:
    """Fetch all settings parsed into their respective Python types."""
    data: dict[str, Any] = {}

    for x in records:
        val = None
        if x.value_type == "boolean":
            val = x.value == "true"
        elif x.value_type == "integer":
            if isinstance(x.value, int):
                val = x.value
            else:
                try:
                    val = int(x.value)  # type: ignore
                except (ValueError, TypeError):
                    val = None
        elif x.value_type == "string":
            val = None if x.value is None else str(x.value)

        if val is None:
            logger.warning("Could not parse setting %s with value %s", x.key, x.value)

        data[x.key] = val

    return data


class SettingsService(CRUDService[SettingRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, SettingRecord)

    def list_settings(self) -> list[SettingRecord]:
        return self.list_all()

    def get_all_settings_raw(self) -> list[dict[str, Any]]:
        """Fetch a setting by key."""
        return [x.to_json() for x in self.list_settings()]

    def get_all_settings_ready(self) -> dict[str, Any]:
        """Fetch all settings parsed into their respective Python types."""
        return format_values(self.list_settings())

    def get_setting_by_key(self, key: str) -> SettingRecord | None:
        """Fetch a setting by key."""
        return self.get_by(key=key)

    def get_setting_by_id(self, setting_id: int) -> SettingRecord | None:
        return self.get_record_by_id(setting_id)

    def update_setting(
        self,
        key: str,
        value: Any,
        value_type: str = "string",
        title: str | None = None,
    ) -> bool:
        """
        Update an existing setting.
        """
        record = self.get_by(key=key)
        if not record:
            return False

        if not value_type:
            value_type = record.value_type

        data = {
            "value": _serialize_value(value, value_type),
        }
        if title:
            data["title"] = title
        try:
            self.update(record, **data)
            return True
        except Exception as e:
            logger.error("Could not update setting %s: %s", key, e)
            return False

    def create_setting(
        self,
        key: str,
        title: str,
        value_type: str = "boolean",
        value: Any | None = None,
    ) -> SettingRecord | None:
        """
        Create new setting.
        """
        key = key.strip()
        title = title.strip()
        if not key:
            raise ValueError("Key is required")
        if not title:
            raise ValueError("Title is required")

        default_value_types = {
            "boolean": "false",
            "integer": "0",
        }
        if value is None:
            value = default_value_types.get(value_type, "")

        try:
            return self.create(
                key=key,
                title=title,
                value_type=value_type,
                value=str(value) if value is not None else None,
            )
        except Exception as exc:
            logger.error("Failed to create new record: %s", exc)
            return None

    def delete_setting_by_key(self, key: str) -> bool:
        record = self.get_by(key=key)
        if record is None:
            return False

        return self.delete_record(record)


__all__ = [
    "SettingsService",
]
