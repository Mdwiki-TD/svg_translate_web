from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar

from ...extensions import db
from . import delete_service

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=db.Model)


class DbService(Generic[ModelT]):
    """Shared database service helpers for SQLAlchemy model services."""

    model: type[ModelT]

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    def list_records(self) -> list[ModelT]:
        """List all records for the configured model.

        Returns:
            All model records, or an empty list if the query fails.
        """
        try:
            return db.session.query(self.model).all()
        except Exception as exc:
            logger.error("Error listing %s records: %s", self.model.__name__, exc)
            return []

    def get_record_by_id(self, record_id: int) -> ModelT | None:
        """Get a record by primary key.

        Args:
            record_id: Primary key value for the configured model.

        Returns:
            The matching record, or None when missing or when the query fails.
        """
        try:
            return db.session.get(self.model, record_id)
        except Exception as exc:
            logger.error("Error getting %s id=%s: %s", self.model.__name__, record_id, exc)
            return None

    def add_record(self, data: dict[str, Any]) -> ModelT | None:
        """Add a record for the configured model.

        Args:
            data: Field values used to construct the model instance.

        Returns:
            The created record, or None when creation fails.
        """
        try:
            record = self.model(**data)
            db.session.add(record)
            db.session.commit()
            return record
        except Exception as exc:
            db.session.rollback()
            logger.error("Error adding %s: %s", self.model.__name__, exc)
            return None

    def update_record(self, record_id: int, data: dict[str, Any]) -> ModelT | None:
        """Update a record by primary key with the provided values.

        Args:
            record_id: Primary key value for the configured model.
            data: Field values to apply to the record.

        Returns:
            The updated record, or None when missing or when the update fails.
        """
        try:
            record = self.get_record_by_id(record_id)
            if record is None:
                return None
            for key, value in data.items():
                setattr(record, key, value)
            db.session.commit()
            return record
        except Exception as exc:
            db.session.rollback()
            logger.error("Error updating %s id=%s: %s", self.model.__name__, record_id, exc)
            return None

    def delete(self, record_id: Any) -> bool:
        """Delete a record by primary key.

        Args:
            record_id: Primary key value for the configured model.

        Returns:
            True when a row was deleted, otherwise False.
        """
        if record_id is None:
            return False

        return delete_service.delete_record_by_pk(self.model, record_id)

__all__ = [
    "DbService",
]
