from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db

logger = logging.getLogger(__name__)


class OwidChartRecord(db.Model):  # type: ignore
    """
    Represents the main pure owid_charts table, completely decoupled from template logic.
    CREATE TABLE `owid_charts` (
        `chart_id` int(11) NOT NULL AUTO_INCREMENT,
        `slug` varchar(255) NOT NULL,
        `title` varchar(500) NOT NULL,
        `has_map_tab` tinyint(1) DEFAULT 0,
        `max_time` int(11) DEFAULT NULL,
        `min_time` int(11) DEFAULT NULL,
        `default_tab` varchar(50) DEFAULT NULL,
        `owid_variable_id` int(11) DEFAULT NULL,
        `is_published` tinyint(1) DEFAULT 0,
        `single_year_data` tinyint(1) DEFAULT 0,
        `len_years` int(11) DEFAULT NULL,
        `has_timeline` tinyint(1) DEFAULT 0,
        `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
        `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (`chart_id`),
        UNIQUE KEY `unique_slug` (`slug`),
        KEY `idx_slug` (`slug`),
        KEY `idx_published` (`is_published`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    __tablename__ = "owid_charts"

    # Core Columns
    chart_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    has_map_tab: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)
    max_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_tab: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owid_variable_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)
    single_year_data: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)
    len_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_timeline: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )

    # Table-level indexes as requested by the original CREATE TABLE DDL
    # __table_args__ = ( Index("idx_slug", "slug"), Index("idx_published", "is_published"), )

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the pure model instance into a dictionary."""
        data: dict[str, Any] = {}
        table_keys = [
            "chart_id",
            "slug",
            "title",
            "has_map_tab",
            "max_time",
            "min_time",
            "default_tab",
            "owid_variable_id",
            "is_published",
            "single_year_data",
            "len_years",
            "has_timeline",
            "created_at",
            "updated_at",
        ]
        for column in table_keys:
            value = getattr(self, column)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column] = value

        return data


__all__ = [
    "OwidChartRecord",
]
