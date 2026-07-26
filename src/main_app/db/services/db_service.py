from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar

from ...extensions import db

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=db.Model)


class DbService(Generic[ModelT]):
    """Shared database service helpers for SQLAlchemy model services."""

    model: type[ModelT]

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    def delete(self, record_id: Any) -> bool:
        """Delete a record by primary key.

        Args:
            record_id: Primary key value for the configured model.

        Returns:
            True when a row was deleted, otherwise False.
        """
        if record_id is None:
            return False

        try:
            record = db.session.get(self.model, record_id)
            if not record:
                return False

            db.session.delete(record)
            db.session.commit()
            return True
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Error deleting {self.model.__name__} with PK {record_id}: {exc}")
            return False


__all__ = [
    "DbService",
]
