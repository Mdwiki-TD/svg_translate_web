"""
Mixins for SQLAlchemy 2.0 models.

These are NOT standalone bases — they are mixed into models
that inherit from db.Model (the Flask-SQLAlchemy declarative base).
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds created_at / updated_at to any model."""

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


__all__ = [
    "TimestampMixin",
]
