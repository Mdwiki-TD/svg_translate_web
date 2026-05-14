from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TemplateNeedUpdateRecord:
    """
    Representation of a template.
    """

    id: int
    template_title: str | None = None
    slug: str | None = None
    chart_year: int | None = None
    template_year: int | None = None
    difference: int | None = None

    def __post_init__(self):
        if self.template_year is not None and self.chart_year is not None:
            self.difference = (self.chart_year or 0) - (self.template_year or 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "template_title": self.template_title,
            "slug": self.slug,
            "chart_year": self.chart_year,
            "template_year": self.template_year,
            "difference": self.difference,
        }
