"""
Flask data base initialization.
"""

from __future__ import annotations

import logging
from typing import Any

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


# expire_on_commit=False preserves current behavior where objects
# remain accessible after commit without triggering new queries.
# (The existing engine.py uses sessionmaker(expire_on_commit=False))
db = SQLAlchemy(
    model_class=BaseModel,
    session_options={"expire_on_commit": False},
)


__all__ = [
    "BaseModel",
    "db",
]
