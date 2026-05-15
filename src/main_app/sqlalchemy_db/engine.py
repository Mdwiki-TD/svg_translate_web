"""
engine.py - Legacy module kept for backward compatibility.

The LONGTEXT custom type is preserved here as it's used by models.
All other functionality (BaseDb, init_db, get_session) has been replaced
by Flask-SQLAlchemy (see extensions.py).
"""

from __future__ import annotations

import logging

from sqlalchemy import Text
from sqlalchemy.dialects.mysql import LONGTEXT as LONGTEXTSQLALCHEMY
from sqlalchemy.types import TypeDecorator

logger = logging.getLogger(__name__)


class LONGTEXT(TypeDecorator):
    """LONGTEXT for MySQL, Text for everything else."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(LONGTEXTSQLALCHEMY())
        return dialect.type_descriptor(Text())


__all__ = [
    "LONGTEXT",
]
