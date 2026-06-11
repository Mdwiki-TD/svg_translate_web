from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db

logger = logging.getLogger(__name__)


class OwidSlugRedirectRecord(db.Model):
    """
    CREATE TABLE `owid_slug_redirects` (
        `id` int(11) NOT NULL AUTO_INCREMENT,
        `slug` varchar(255) NOT NULL,
        `redirect_to` varchar(255) NOT NULL,
        `should_be_replaced` tinyint(1) DEFAULT 0,
        `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
        PRIMARY KEY (`id`),
        UNIQUE KEY `unique_slug_redirect` (`slug`, `redirect_to`),
        KEY `idx_slug` (`slug`),
        KEY `idx_redirect_to` (`redirect_to`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "owid_slug_redirects"

    # Explicit table arguments to match indices and unique constraints from raw SQL
    __table_args__ = (
        UniqueConstraint("slug", "redirect_to", name="unique_slug_redirect"),
        Index("idx_slug", "slug"),
        Index("idx_redirect_to", "redirect_to"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    redirect_to: Mapped[str] = mapped_column(String(255), nullable=False)
    should_be_replaced: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())

    def to_dict(self) -> dict[str, Any]:
        """Serializes the pure model instance into a dictionary."""
        data: dict[str, Any] = {}
        table_keys = [
            "id",
            "slug",
            "redirect_to",
            "should_be_replaced",
            "created_at",
        ]
        for column in table_keys:
            value = getattr(self, column)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column] = value
        return data


__all__ = [
    "OwidSlugRedirectRecord",
]
