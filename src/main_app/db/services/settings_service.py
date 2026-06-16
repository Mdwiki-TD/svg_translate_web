from __future__ import annotations

import logging
from typing import Any

from ...extensions import db
from ..models.settings import SettingRecord
from .delete_service import delete_setting
from .utils import db_guard, db_guard_rollback

logger = logging.getLogger(__name__)


def _parse_setting_value(v_type: str, raw_val: str) -> tuple[Any, bool]:
    """Returns (value, success)"""
    if v_type == "boolean":
        return raw_val == "on", True
    elif v_type == "integer":
        try:
            return int(raw_val), True
        except (TypeError, ValueError):
            return 0, True
    else:
        return raw_val, True


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
    """List all settings."""
    return db.session.query(SettingRecord).all()


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


def get_setting_by_key(key: str) -> SettingRecord:
    """Fetch a setting by key."""
    return db.session.query(SettingRecord).filter(SettingRecord.key == key).first()


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


@db_guard_rollback
def update_setting_bool(
    key: str,
    value: Any,
    value_type: str | None = None,
    title: str | None = None,
) -> bool:
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
    return True


def create_setting(key: str, title: str, value_type: str, value: str | None = None) -> bool:
    """
    Create new setting.
    """
    default_value_types = {
        "boolean": "false",
        "integer": "0",
    }

    value = value or default_value_types.get(value_type, "")

    setting = SettingRecord(key=key, title=title, value=value, value_type=value_type)
    db.session.add(setting)
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def settings_update_form(request_form) -> tuple[list[str], list[str]]:
    all_settings = get_all_settings_raw()
    failed_keys: list[str] = []
    deleted_keys: list[str] = []

    for s in all_settings:
        key = s["key"]
        v_type = s["value_type"]
        form_key = f"setting_{key}"
        delete_key = f"delete_{key}"

        # Check if marked for deletion
        if request_form.get(delete_key) == "on":
            if delete_setting(key):
                deleted_keys.append(key)
            else:
                failed_keys.append(key)
            continue

        if v_type == "boolean":
            raw_val = request_form.get(form_key, "")
        elif form_key in request_form:
            raw_val = request_form.get(form_key, "")
        else:
            continue

        value, success = _parse_setting_value(v_type, raw_val)
        if not success or not update_setting(key, value, v_type):
            failed_keys.append(key)

    return failed_keys, deleted_keys


__all__ = [
    "get_setting_by_key",
    "get_all_settings_raw",
    "update_setting",
    "create_setting",
    "settings_update_form",
    "list_settings",
    "get_all_settings_ready",
]
