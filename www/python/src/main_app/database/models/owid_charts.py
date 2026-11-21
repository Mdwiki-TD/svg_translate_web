from __future__ import annotations

import logging

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db_base import Model
from .base import TimestampMixin

logger = logging.getLogger(__name__)


class OwidChartRecord(TimestampMixin, Model):
    """
    Represents the main pure owid_charts table, completely decoupled from template logic.
    CREATE TABLE `owid_charts` (
        `chart_id` int(11) NOT NULL AUTO_INCREMENT,
        `slug` varchar(255) NOT NULL,
        `title` varchar(500) NOT NULL,
        `source` varchar(2048) NOT NULL DEFAULT '',
        `has_map_tab` tinyint(1) DEFAULT 0,
        `max_time` int(11) DEFAULT NULL,
        `min_time` int(11) DEFAULT NULL,
        `default_tab` varchar(50) DEFAULT NULL,
        `owid_variable_id` int(11) DEFAULT NULL,
        `is_published` tinyint(1) DEFAULT 0,
        `single_year_data` tinyint(1) DEFAULT 0,
        `len_years` int(11) DEFAULT NULL,
        `has_timeline` tinyint(1) DEFAULT 0,
        `status_404` int(11) DEFAULT NULL,
        `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
        `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (`chart_id`),
        UNIQUE KEY `unique_slug` (`slug`),
        KEY `idx_slug` (`slug`),
        KEY `idx_published` (`is_published`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    __tablename__ = "owid_charts"

    __table_args__ = (
        UniqueConstraint("slug", name="unique_slug"),
        Index("idx_slug", "slug"),
        Index("idx_published", "is_published"),
    )

    chart_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(2048), default="", server_default="")

    has_map_tab: Mapped[bool] = mapped_column(server_default="0", default=False)
    max_time: Mapped[int | None] = mapped_column(nullable=True)
    min_time: Mapped[int | None] = mapped_column(nullable=True)
    default_tab: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owid_variable_id: Mapped[int | None] = mapped_column(nullable=True)
    is_published: Mapped[bool] = mapped_column(server_default="0", default=False)
    single_year_data: Mapped[bool] = mapped_column(server_default="0", default=False)
    len_years: Mapped[int | None] = mapped_column(nullable=True)
    has_timeline: Mapped[bool] = mapped_column(server_default="0", default=False)
    status_404: Mapped[int | None] = mapped_column(nullable=True)


__all__ = [
    "OwidChartRecord",
]
