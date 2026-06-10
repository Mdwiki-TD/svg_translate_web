from __future__ import annotations

import logging

from sqlalchemy import Boolean, Column, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.orm import validates

from ...extensions import db
from ...shared.decode_bytes import coerce_bytes

logger = logging.getLogger(__name__)


class UsersRecord(db.Model):
    """Stable user identity — source of truth for user_id and username.

    CREATE TABLE `users` (
        `user_id` int NOT NULL AUTO_INCREMENT,
        `username` varchar(255) NOT NULL,
        `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `can_run_jobs` tinyint(1) NOT NULL DEFAULT '0',
        `can_run_bg_jobs` tinyint(1) NOT NULL DEFAULT '0',
        PRIMARY KEY (`user_id`),
        UNIQUE KEY `uq_users_username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    can_run_jobs = Column(Boolean, nullable=False, default=False, server_default="0")
    can_run_bg_jobs = Column(Boolean, nullable=False, default=False, server_default="0")

    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(
        String(255),
        db.ForeignKey("users.username", ondelete="CASCADE", onupdate="CASCADE"),
        unique=True,
        nullable=False,
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")

    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


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

    user_id = Column(
        Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    access_token = Column(LargeBinary(1024), nullable=False)
    access_secret = Column(LargeBinary(1024), nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )
    last_used_at = Column(DateTime, nullable=True, server_default=func.current_timestamp())
    rotated_at = Column(DateTime, nullable=True)

    user = db.relationship("UsersRecord", backref=db.backref("token", uselist=False))

    @validates("access_token", "access_secret")
    def validate_bytes(self, key, value):
        return coerce_bytes(value)


__all__ = [
    "AdminUserRecord",
    "UserTokenRecord",
    "UsersRecord",
]
