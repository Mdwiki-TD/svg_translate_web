from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(255), nullable=False, unique=True)
    redirect_to = Column(String(255), nullable=False)
    should_be_replaced = Column(Boolean, server_default="0", default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for column in self.__table__.columns:  # pyright: ignore[reportAttributeAccessIssue]
            value = getattr(self, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column.name] = value
        return data


__all__ = [
    "OwidSlugRedirectRecord",
]
