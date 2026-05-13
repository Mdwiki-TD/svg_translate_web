from __future__ import annotations

import json
import logging
from typing import Any

# from ..shared.models import SettingRecord
from ..config import settings
from ..db import has_db_config
from ..db.db_Settings import SettingsDB

logger = logging.getLogger(__name__)
_SETTINGS_STORE: SettingsDB | None = None


def get_settings_db() -> SettingsDB:
    """
    Return the singleton settings database store, initializing it on first access.
    """
    global _SETTINGS_STORE

    if _SETTINGS_STORE is None:
        if not has_db_config():
            raise RuntimeError("SettingsDB requires database configuration; no fallback store is available.")

        try:
            _SETTINGS_STORE = SettingsDB(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL settings store")
            raise RuntimeError("Unable to initialize settings store") from exc

    return _SETTINGS_STORE


def _parse_setting_value(v_type: str, raw_val: str) -> tuple[any, bool]:
    """Returns (value, success)"""
    if v_type == "boolean":
        return raw_val == "on", True
    elif v_type == "integer":
        try:
            return int(raw_val), True
        except ValueError:
            return 0, True
    elif v_type == "json":
        try:
            return json.loads(raw_val), True
        except Exception:
            return None, False
    else:
        return raw_val, True


def get_all_settings_raw() -> list[dict[str, Any]]:
    """Fetch a setting by key."""
    store = get_settings_db()
    return store.get_raw_all()


def delete_setting(key: str) -> bool:
    """delete a setting by key."""
    store = get_settings_db()
    return store.delete_setting(key)


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
    return store.update_setting(key, value, value_type, title)


def create_setting(key: str, title: str, value_type: str) -> bool:
    """
    Create new setting.
    """
    store = get_settings_db()

    if value_type == "boolean":
        value = False
    elif value_type == "integer":
        value = 0
    elif value_type == "json":
        value = {}
    else:
        value = ""

    return store.create_setting(key, title, value_type, value)


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
    "get_all_settings_raw",
    "delete_setting",
    "update_setting",
    "create_setting",
    "settings_update_form",
]
