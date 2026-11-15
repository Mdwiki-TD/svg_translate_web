from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from ...extensions import Model, db
from ...services.utils.decode_bytes import coerce_bytes
from .base import TimestampMixin

logger = logging.getLogger(__name__)


class UserRecord(Model):
    """
    Stable user identity — source of truth for user_id and username.
    """

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    can_run_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    can_run_bg_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        default=func.current_timestamp(),
    )

    # One-to-One relationship with UserTokenRecord using the modern SQLAlchemy 2.0 style
    token: Mapped[UserTokenRecord | None] = relationship(back_populates="user", uselist=False)


class AdminUserRecord(TimestampMixin, Model):
    """
    Admin/admin role — username references users.username.
    """

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Modern approach for defining foreign keys
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False
    )

    # Python application default and database-level server default configuration
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("1"))

    def __repr__(self) -> str:
        return f"<Admin id={self.id} username={self.username!r} is_active={self.is_active}>"


class UserTokenRecord(TimestampMixin, Model):
    """
    OAuth credentials — child of users table.
    """

    __tablename__ = "user_tokens"
    __json_exclude__ = frozenset({"access_token", "access_secret"})

    # Modern consolidated syntax for a field acting as both a Primary Key and a Foreign Key
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )

    # LargeBinary maps strictly to Python bytes
    access_token: Mapped[bytes] = mapped_column(db.LargeBinary(1024), nullable=False)
    access_secret: Mapped[bytes] = mapped_column(db.LargeBinary(1024), nullable=False)

    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True, server_default=func.current_timestamp())
    rotated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Clean explicit relationship mapping matching SQLAlchemy 2.0 recommendations via back_populates
    user: Mapped[UserRecord] = relationship(back_populates="token")

    @validates("access_token", "access_secret")
    def validate_bytes(self, key, value) -> bytes:
        return coerce_bytes(value)


__all__ = [
    "AdminUserRecord",
    "UserTokenRecord",
    "UserRecord",
]
