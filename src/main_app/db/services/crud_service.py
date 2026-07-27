from __future__ import annotations

import logging
from typing import Any, TypeVar

from ...extensions import db

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=db.Model)


class CRUDService[ModelT: db.Model]:
    """Shared database service helpers for SQLAlchemy model services."""

    model: type[ModelT]

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model
        self.session = db.session

    def list_records(self) -> list[ModelT]:
        """List all records for the configured model.

        Returns:
            All model records, or an empty list if the query fails.
        """
        try:
            return self.session.query(self.model).all()
        except Exception as exc:
            logger.error("Error listing %s records: %s", self.model.__name__, exc)
            return []

    def list_all(self) -> list[ModelT]:
        try:
            return self.session.query(self.model).all()
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
            return self.session.get(self.model, record_id)
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
            self.session.add(record)
            self.session.commit()
            return record
        except Exception as exc:
            self.session.rollback()
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
            self.session.commit()
            return record
        except Exception as exc:
            self.session.rollback()
            logger.error("Error updating %s id=%s: %s", self.model.__name__, record_id, exc)
            return None

    def delete(self, pk_value: Any) -> bool:
        """Delete a record by primary key.

        Args:
            pk_value: Primary key value for the configured model.

        Returns:
            True when a row was deleted, otherwise False.
        """
        if pk_value is None:
            return False

        """
        Generic helper to delete a record by its primary key.
        Returns True if deleted, False otherwise.
        """
        if pk_value is None:
            return False

        try:
            # Use session.get() as it is efficient and looks up by primary key
            record = self.session.get(self.model, pk_value)
            if record:
                self.session.delete(record)
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} with PK {pk_value}: {e}")
            self.session.rollback()
            return False


__all__ = [
    "CRUDService",
]
