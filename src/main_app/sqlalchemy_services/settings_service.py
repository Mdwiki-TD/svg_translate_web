from __future__ import annotations

import logging
from typing import List, Optional, Any

from ..sqlalchemy_models.settings import SettingRecord
from ..engine import get_session

logger = logging.getLogger(__name__)


def get_setting(key: str) -> Optional[SettingRecord]:
    """Fetch a setting by key."""
    with get_session() as session:
        return session.query(SettingRecord).filter(SettingRecord.key == key).first()


def set_setting(key: str, value: Any, title: Optional[str] = None, value_type: str = "string") -> SettingRecord:
    """Set a setting value."""
    with get_session() as session:
        setting = session.query(SettingRecord).filter(SettingRecord.key == key).first()
        if setting:
            setting.value = str(value)
            if title:
                setting.title = title
        else:
            setting = SettingRecord(key=key, value=str(value), title=title or key, value_type=value_type)
            session.add(setting)
        session.commit()
        session.refresh(setting)
        return setting


def list_settings() -> List[SettingRecord]:
    """List all settings."""
    with get_session() as session:
        return session.query(SettingRecord).all()


__all__ = [
    "get_setting",
    "set_setting",
    "list_settings",
]
