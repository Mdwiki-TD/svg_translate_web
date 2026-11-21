"""
Flask data base initialization.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class BaseModel(DeclarativeBase):
    """Base model providing a generic to_json() for all records."""

    # Column names that must never be serialized. Override in subclasses.
    __json_exclude__: ClassVar[frozenset[str]] = frozenset()

    def to_json(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for column in self.__table__.columns:  # type: ignore
            if column.name in self.__json_exclude__:
                continue
            value = getattr(self, column.name)  # type: ignore
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column.name] = value  # type: ignore
        return data

    @classmethod
    def load(cls, **kwargs: Any):
        args = {key: value for key, value in kwargs.items() if hasattr(cls, key)}
        return cls(**args)


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

if TYPE_CHECKING:
    Model = BaseModel
else:
    Model = db.Model

__all__ = [
    "Model",
    "BaseModel",
    "db",
    "metadata",
]
