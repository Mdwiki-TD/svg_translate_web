"""
SQLAlchemy-based service for managing settings.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ..models import SettingRecord
from .utils import db_guard

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


def list_settings() -> list[SettingRecord]:
    """Return all setting records."""
    orm_objs = db.session.query(SettingRecord).all()
    return orm_objs


def get_all_settings_raw() -> list[dict[str, Any]]:
    """Fetch a setting by key."""
    return [x.to_dict() for x in list_settings()]


def get_all_settings_ready() -> dict[str, Any]:
    """Fetch all settings parsed into their respective Python types."""
    records: dict[str, Any] = {}

    for x in list_settings():
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
            val = str(x.value)

        if val is None:
            logger.warning("Could not parse setting %s with value %s", x.key, x.value)

        records[x.key] = val

    return records


def get_setting_by_key(key: str) -> SettingRecord | None:
    """Fetch a setting by key."""
    return db.session.query(SettingRecord).filter(SettingRecord.key == key).first()


def get_setting_by_id(setting_id: int) -> SettingRecord | None:
    """Get a setting record by ID."""
    orm_obj = db.session.get(SettingRecord, setting_id)
    if not orm_obj:
        logger.warning(f"Setting record with ID {setting_id} not found")
        return None
    return orm_obj


@db_guard(default_return=False)
def update_setting(
    key: str,
    value: Any,
    value_type: str = "string",
    title: str | None = None,
) -> SettingRecord:
    """
    Update an existing setting.
    """
    setting = db.session.query(SettingRecord).filter(SettingRecord.key == key).first()
    if not setting:
        return False

    if not value_type:
        value_type = setting.value_type

    setting.value = _serialize_value(value, value_type)
    if title:
        setting.title = title
    db.session.commit()
    return setting


def create_setting(
    key: str,
    title: str,
    value_type: str = "boolean",
    value: Any | None = None,
) -> bool:
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

    value = value or default_value_types.get(value_type, "")

    orm_obj = SettingRecord(
        key=key,
        title=title,
        value_type=value_type,
        value=str(value) if value is not None else None,
    )
    db.session.add(orm_obj)
    try:
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
    except Exception:
        db.session.rollback()
        return False


__all__ = [
    "list_settings",
    "get_setting_by_id",
    "get_setting_by_key",
    "get_all_settings_raw",
    "update_setting",
    "create_setting",
    "list_settings",
    "get_all_settings_ready",
]
