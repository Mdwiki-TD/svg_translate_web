""" """

from __future__ import annotations

import logging
from typing import Any

from ...extensions import db


logger = logging.getLogger(__name__)


def delete_record_by_pk(model: type[db.Model], pk_value: Any) -> bool:  # type: ignore
    """
    Generic helper to delete a record by its primary key.
    Returns True if deleted, False otherwise.
    """
    if pk_value is None:
        return False

    try:
        # Use session.get() as it is efficient and looks up by primary key
        record = db.session.get(model, pk_value)
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting {model.__name__} with PK {pk_value}: {e}")
        db.session.rollback()
        return False

__all__ = [
    "delete_record_by_pk",
]
