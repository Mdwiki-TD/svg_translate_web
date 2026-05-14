from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TemplateNeedUpdateRecord:
    """
    """

    __tablename__ = "templates_need_update"

    id: int
    template_title: str | None = None
    slug: str | None = None
    chart_year: int | None = None
    template_year: int | None = None
    difference: int | None = None

    __table_args__ = (
        # Prevent SQLAlchemy from trying to create this as a table
        {
            "info": {
                "is_view": True,
                "create_query": """
                    CREATE VIEW
                        templates_need_update AS
                    select
                        t.id AS template_id,
                        t.title AS template_title,
                        t.slug AS slug,
                        t.last_world_year AS last_world_year
                        c.max_time AS max_time,
                    from owid_charts c
                            join templates t on t.slug = c.slug
                    where
                        t.last_world_year <> c.max_time
                        and t.last_world_year is not null
                    ;
                    """,
            }
        },
    )

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


class OwidChartTemplateRecord:
    """
    """

    __tablename__ = "owid_charts_templates"

    chart_id: int
    template_id: int | None = None
    template_title: str | None = None
    template_source: str | None = None

    __table_args__ = (
        # Prevent SQLAlchemy from trying to create this as a table
        {
            "info": {
                "is_view": True,
                "create_query": """
                    CREATE VIEW
                        owid_charts_templates AS
                    select
                        c.chart_id AS chart_id,
                        t.id AS template_id,
                        t.title AS template_title
                    from owid_charts c
                        left join templates t on t.slug = c.slug
                    ;
                    """,
            }
        },
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "template_id": self.template_id,
            "template_title": self.template_title,
        }


__all__ = [
    "TemplateNeedUpdateRecord",
    "OwidChartTemplateRecord",
]
