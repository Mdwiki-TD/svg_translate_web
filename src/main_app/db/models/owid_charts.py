from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OwidChartRecord:
    """
    CREATE TABLE `owid_charts` (
      `chart_id` int(11) NOT NULL AUTO_INCREMENT,
      `slug` varchar(255) NOT NULL,
      `title` varchar(500) NOT NULL,
      `has_map_tab` tinyint(1) DEFAULT 0,
      `max_time` int(11) DEFAULT NULL,
      `min_time` int(11) DEFAULT NULL,
      `default_tab` varchar(50) DEFAULT NULL,
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "owid_charts"

    chart_id: int
    slug: str
    title: str
    has_map_tab: bool
    max_time: int | None
    min_time: int | None
    default_tab: str | None
    is_published: bool
    single_year_data: bool
    len_years: int | None
    has_timeline: bool
    created_at: Any | None = None
    updated_at: Any | None = None
    template_id: int | None = None
    template_title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "slug": self.slug,
            "title": self.title,
            "has_map_tab": self.has_map_tab,
            "max_time": self.max_time,
            "min_time": self.min_time,
            "default_tab": self.default_tab,
            "is_published": self.is_published,
            "single_year_data": self.single_year_data,
            "len_years": self.len_years,
            "has_timeline": self.has_timeline,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "template_id": self.template_id,
            "template_title": self.template_title,
        }


__all__ = [
    "OwidChartRecord",
]
