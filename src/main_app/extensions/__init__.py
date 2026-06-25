"""
Flask extensions instantiation.

IMPORTANT: This file must NOT import any application modules.
Only third-party extensions should be instantiated here.
This prevents circular imports when models/services import `db`.
"""

from __future__ import annotations

import logging
from typing import Any

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model

logger = logging.getLogger(__name__)


class BaseModel(Model):
    """Base model providing a generic to_dict() for all records."""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for column in self.__table__.columns:  # type: ignore
            value = getattr(self, column.name)  # type: ignore
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column.name] = value  # type: ignore
        return data

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


def _commit(db: SQLAlchemy) -> None:
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Database commit failed; transaction rolled back.")
        raise


# expire_on_commit=False preserves current behavior where objects
# remain accessible after commit without triggering new queries.
# (The existing engine.py uses sessionmaker(expire_on_commit=False))
db = SQLAlchemy(
    model_class=BaseModel,
    session_options={"expire_on_commit": False},
)

migrate = Migrate()

__all__ = [
    "BaseModel",
    "db",
    "migrate",
]
