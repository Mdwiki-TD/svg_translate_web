from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OwidChartRecord:
    """Representation of an OWID chart record."""

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
    template_source: str | None = None

    def __post_init__(self):
        if not self.template_source and self.slug:
            self.template_source = f"https://ourworldindata.org/grapher/{self.slug}"

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
            "template_source": self.template_source,
        }
