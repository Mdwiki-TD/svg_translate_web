from __future__ import annotations

import logging
from typing import Any

from ...extensions import db
from .delete_service import delete_record_by_pk

logger = logging.getLogger(__name__)


class DbService:
    def __init__(self, model: type[db.Model]) -> None:
        self.model = model

    def list_records(self) -> list[Any]:
        try:
            return db.session.query(self.model).all()
        except Exception as exc:
            logger.error("Error getting records: %s", str(exc))
            return []

    def get_record_by_id(self, record_id: int) -> Any | None:
        try:
            return db.session.get(self.model, record_id)
        except Exception as exc:
            logger.error("Error getting record: %s", str(exc))
            return None

    def add_record(self, data: dict[str, Any]) -> Any | None:
        try:
            temp_data = {
                key: value for key, value in data.items() if value is not None and hasattr(self.model, key)
            }
            record = self.model(**temp_data)
            db.session.add(record)
            db.session.commit()
            db.session.refresh(record)
            return record
        except Exception as exc:
            db.session.rollback()
            logger.error("Error adding record: %s", str(exc))
            return None

    def add_recoed(self, data: dict[str, Any]) -> Any | None:
        """Alias for add_record to support potential typos or user compatibility."""
        return self.add_record(data)

    def update_data(self, record_id: int, data: dict[str, Any]) -> Any | None:
        try:
            record = db.session.get(self.model, record_id)
            if not record:
                return None
            for key, value in data.items():
                if value is not None and hasattr(self.model, key):
                    setattr(record, key, value)
            db.session.commit()
            db.session.refresh(record)
            return record
        except Exception as exc:
            db.session.rollback()
            logger.error("Error updating record: %s", str(exc))
            return None

    def delete(self, record_id: int) -> bool:
        return delete_record_by_pk(self.model, record_id)


__all__ = [
    "DbService",
]
