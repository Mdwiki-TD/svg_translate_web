"""
Flask data base initialization.
"""

from __future__ import annotations

import logging
from typing import Any

from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model
from sqlalchemy import MetaData

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

# Naming convention for constraints (required for reliable Alembic migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

# Flask-SQLAlchemy instance
# Uses existing BaseDb (DeclarativeBase) as model_class so all existing
# models continue to work unchanged.
db = SQLAlchemy(
    model_class=BaseModel,
    metadata=metadata,
    session_options={"expire_on_commit": False},
)


__all__ = [
    "BaseModel",
    "db",
    "metadata",
]
