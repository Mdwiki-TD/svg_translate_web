from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OwidChartTemplateRecord:
    """ """

    __tablename__ = "owid_charts_templates"

    chart_id: int
    template_id: int | None = None
    template_title: str | None = None
    # template_source: str | None = None

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
    "OwidChartTemplateRecord",
]
