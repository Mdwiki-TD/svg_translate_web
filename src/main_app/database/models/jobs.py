from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db

logger = logging.getLogger(__name__)


class JobRecord(db.Model):
    """
    CREATE TABLE `jobs` (
        `id` int NOT NULL AUTO_INCREMENT,
        `job_type` varchar(255) NOT NULL,
        `username` varchar(255) NOT NULL,
        `status` varchar(50) NOT NULL DEFAULT 'pending',
        `started_at` datetime DEFAULT NULL,
        `completed_at` datetime DEFAULT NULL,
        `result_file` varchar(500) DEFAULT NULL,
        `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `is_running` tinyint DEFAULT NULL,
        PRIMARY KEY (`id`),
        UNIQUE KEY `idx_unique_active_job` (`job_type`,`is_running`),
        KEY `username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    NOTE: username has no FK — jobs persist independently of user accounts.
    """

    __tablename__ = "jobs"

    __table_args__ = (
        # Unique constraint combining job_type and is_running
        UniqueConstraint("job_type", "is_running", name="idx_unique_active_job"),
        # Keep the standard index for username if needed
        Index("username", "username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'pending'"))

    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    result_file: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    is_running: Mapped[int | None] = mapped_column(nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the pure model instance into a dictionary."""
        data: dict[str, Any] = {}
        table_keys = [
            "id",
            "job_type",
            "username",
            "status",
            "started_at",
            "completed_at",
            "result_file",
            "created_at",
            "updated_at",
            "is_running",
        ]
        for column in table_keys:
            value = getattr(self, column)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column] = value

        return data


__all__ = [
    "JobRecord",
]
