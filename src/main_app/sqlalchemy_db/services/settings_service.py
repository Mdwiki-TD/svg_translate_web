from __future__ import annotations

import json
import logging
from typing import Any

from ..engine import get_session
from ..models.settings import SettingRecord

logger = logging.getLogger(__name__)


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


def list_settings() -> list[SettingRecord]:
    """List all settings."""
    with get_session() as session:
        return session.query(SettingRecord).all()


def get_all_settings_raw() -> list[dict[str, Any]]:
    """Fetch a setting by key."""
    return [x.to_dict() for x in list_settings()]


def get_setting_by_key(key: str) -> SettingRecord:
    """Fetch a setting by key."""
    with get_session() as session:
        return session.query(SettingRecord).filter(SettingRecord.key == key).first()


def delete_setting(key: str) -> bool:
    """delete a setting by key."""
    with get_session() as session:
        record = session.query(SettingRecord).filter(SettingRecord.key == key).first()
        if record:
            session.delete(record)
            session.commit()
            return True
        return False


def update_setting(
    key: str,
    value: Any,
    value_type: str = "string",
    title: str | None = None,
) -> SettingRecord:
    """
    Update an existing setting.
    """
    with get_session() as session:
        setting = session.query(SettingRecord).filter(SettingRecord.key == key).first()
        if setting:
            if value_type == "json":
                setting.value = json.dumps(value)
            else:
                setting.value = str(value)
            if title:
                setting.title = title
        else:
            setting = SettingRecord(key=key, value=str(value), title=title or key, value_type=value_type)
            session.add(setting)
        session.commit()
        session.refresh(setting)
        return setting


def create_setting(key: str, title: str, value_type: str) -> bool:
    """
    Create new setting.
    """
    if value_type == "boolean":
        value = False
    elif value_type == "integer":
        value = 0
    elif value_type == "json":
        value = {}
    else:
        value = ""

    with get_session() as session:
        job = SettingRecord(key=key, title=title, value=value, value_type=value_type)
        session.add(job)
        session.commit()
        session.refresh(job)
        return job


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
