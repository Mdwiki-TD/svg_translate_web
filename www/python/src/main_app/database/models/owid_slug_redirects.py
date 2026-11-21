from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ..db_base import Model

logger = logging.getLogger(__name__)


class OwidSlugRedirectRecord(Model):
    """
    CREATE TABLE `owid_slug_redirects` (
        `id` int(11) NOT NULL AUTO_INCREMENT,
        `slug` varchar(255) NOT NULL,
        `redirect_to` varchar(255) NOT NULL,
        `should_be_replaced` tinyint(1) DEFAULT 0,
        `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
        PRIMARY KEY (`id`),
        UNIQUE KEY `unique_slug_redirect` (`slug`, `redirect_to`),
        KEY `idx_slug_n` (`slug`),
        KEY `idx_redirect_to` (`redirect_to`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    __tablename__ = "owid_slug_redirects"

    # Explicit table arguments to match indices and unique constraints from raw SQL
    __table_args__ = (
        UniqueConstraint("slug", "redirect_to", name="unique_slug_redirect"),
        Index("idx_slug_n", "slug"),
        Index("idx_redirect_to", "redirect_to"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255))
    redirect_to: Mapped[str] = mapped_column(String(255))
    should_be_replaced: Mapped[bool | None] = mapped_column(
        nullable=True,
        default=False,
        server_default=text("0"),
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
    )


__all__ = [
    "OwidSlugRedirectRecord",
]
