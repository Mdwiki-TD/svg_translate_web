from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from ...extensions import db
from ...shared.decode_bytes import coerce_bytes

logger = logging.getLogger(__name__)


class UsersRecord(db.Model):
    """Stable user identity — source of truth for user_id and username.

    CREATE TABLE `users` (
      `user_id` int NOT NULL AUTO_INCREMENT,
      `username` varchar(255) NOT NULL,
      `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`user_id`),
      UNIQUE KEY `uq_users_username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())

    can_run_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    can_run_bg_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)

    # One-to-One relationship with UserTokenRecord using the modern SQLAlchemy 2.0 style
    token: Mapped[UserTokenRecord | None] = relationship(back_populates="user", uselist=False)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the pure model instance into a dictionary."""
        data: dict[str, Any] = {}
        table_keys = [
            "user_id",
            "username",
            "created_at",
        ]
        for column in table_keys:
            value = getattr(self, column)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column] = value

        return data



class AdminUserRecord(db.Model):
    """
    Coordinator/admin role — username references users.username.

    CREATE TABLE `admin_users` (
      `id` int NOT NULL AUTO_INCREMENT,
      `username` varchar(255) NOT NULL,
      `is_active` tinyint(1) NOT NULL DEFAULT '0',
      `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
      `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `username` (`username`),
      CONSTRAINT `admin_users_ibfk_1` FOREIGN KEY (`username`)
        REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Modern approach for defining foreign keys
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False
    )

    # Python application default and database-level server default configuration
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("1"))

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    def to_dict(self) -> dict[str, Any]:
        """Serializes the pure model instance into a dictionary."""
        data: dict[str, Any] = {}
        table_keys = [
            "id",
            "username",
            "is_active",
            "created_at",
            "updated_at",
        ]
        for column in table_keys:
            value = getattr(self, column)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column] = value

        return data

    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.id = kwargs.get("id")
        self.username = kwargs.get("username")
        self.is_active = kwargs.get("is_active")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")


class UserTokenRecord(db.Model):
    """
    OAuth credentials — child of users table.

    CREATE TABLE IF NOT EXISTS user_tokens (
      user_id int NOT NULL,
      access_token varbinary(1024) NOT NULL,
      access_secret varbinary(1024) NOT NULL,
      created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      last_used_at datetime DEFAULT NULL,
      rotated_at datetime DEFAULT NULL,
      PRIMARY KEY (user_id),
      CONSTRAINT `user_tokens_ibfk_1` FOREIGN KEY (`user_id`)
        REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
    )
    """

    __tablename__ = "user_tokens"

    # Modern consolidated syntax for a field acting as both a Primary Key and a Foreign Key
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )

    # LargeBinary maps strictly to Python bytes
    access_token: Mapped[bytes] = mapped_column(db.LargeBinary(1024), nullable=False)
    access_secret: Mapped[bytes] = mapped_column(db.LargeBinary(1024), nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True, server_default=func.current_timestamp())
    rotated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Clean explicit relationship mapping matching SQLAlchemy 2.0 recommendations via back_populates
    user: Mapped[UsersRecord] = relationship(back_populates="token")

    @validates("access_token", "access_secret")
    def validate_bytes(self, key, value) -> bytes:
        return coerce_bytes(value)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the pure model instance into a dictionary."""
        data: dict[str, Any] = {}
        table_keys = [
            "user_id",
            "access_token",
            "access_secret",
            "created_at",
            "updated_at",
            "last_used_at",
            "rotated_at",
        ]
        for column in table_keys:
            value = getattr(self, column)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column] = value

        return data


    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.user_id = kwargs.get("user_id")
        self.access_token = kwargs.get("access_token")
        self.access_secret = kwargs.get("access_secret")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        self.last_used_at = kwargs.get("last_used_at")
        self.rotated_at = kwargs.get("rotated_at")

__all__ = [
    "AdminUserRecord",
    "UserTokenRecord",
    "UsersRecord",
]
