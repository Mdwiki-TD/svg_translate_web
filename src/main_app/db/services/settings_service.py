from __future__ import annotations

import json
import logging
from typing import Any

from ..db_Settings import SettingsDB
from ..models import SettingRecord
from .check_db import initialize_db

logger = logging.getLogger(__name__)
_SETTINGS_STORE: SettingsDB | None = None


def get_settings_db() -> SettingsDB:
    """
    Return the singleton settings database store, initializing it on first access.
    """
    global _SETTINGS_STORE

    if _SETTINGS_STORE is None:
        _SETTINGS_STORE = initialize_db(SettingsDB)

    return _SETTINGS_STORE


def _parse_setting_value(value_type: str, raw_val: str) -> tuple[Any, bool]:
    """Returns (value, success)"""
    if value_type == "boolean":
        return raw_val == "on", True
    elif value_type == "integer":
        try:
            return int(raw_val), True
        except ValueError:
            return 0, True
    elif value_type == "json":
        try:
            return json.loads(raw_val), True
        except Exception:
            return None, False
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
    elif value_type == "json":
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def list_settings() -> list[SettingRecord]:
    """List all settings."""
    store = get_settings_db()
    return store.all()


def get_all_settings_raw() -> list[dict[str, Any]]:
    """Fetch a setting by key."""
    store = get_settings_db()
    return store.get_raw_all()


def get_setting_by_key(key: str) -> SettingRecord | None:
    """Fetch a setting by key."""
    store = get_settings_db()
    return store.get_by_key(key)


def delete_setting(key: str) -> bool:
    """delete a setting by key."""
    store = get_settings_db()
    return store.delete(key)


def update_setting(
    key: str,
    value: Any,
    value_type: str | None = None,
    title: str | None = None,
) -> bool:
    """
    Update an existing setting.
    """
    store = get_settings_db()
    # If value_type not provided, retrieve it from the database
    if not value_type:
        record = store.get_by_key(key)
        if not record:
            return False
        value_type = record.value_type

    str_val = _serialize_value(value, value_type)
    return store.update(key, str_val, title)


def create_setting(key: str, title: str, value_type: str) -> bool:
    """
    Create new setting.
    """
    default_value_types = {
        "boolean": "false",
        "integer": "0",
        "json": "{}",
    }

    value = default_value_types.get(value_type, "")

    store = get_settings_db()
    return store.create(key, title, value_type, value)


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
    "delete_setting",
    "update_setting",
    "create_setting",
    "settings_update_form",
    "list_settings",
]
