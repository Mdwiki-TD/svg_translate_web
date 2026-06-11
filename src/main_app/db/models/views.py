from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column
from ...extensions import db

logger = logging.getLogger(__name__)



class TemplateNeedUpdateRecord(db.Model):
    """ """

    __tablename__ = "templates_need_update"

    template_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    last_world_year: Mapped[int | None] = mapped_column(nullable=True)
    max_time: Mapped[int | None] = mapped_column(nullable=True)

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
                        c.max_time AS max_time,
                        t.last_world_year AS last_world_year
                    from
                        owid_charts c
                        join templates t on t.slug = c.slug
                    where
                        t.last_world_year < c.max_time
                        AND c.max_time <= YEAR(now())
                        and t.last_world_year is not null
                    ;
                    """,
            }
        },
    )

    def to_dict(self) -> dict[str, Any]:
        difference = 0
        if self.max_time and self.last_world_year:
            difference = (self.max_time or 0) - (self.last_world_year or 0)
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "slug": self.slug,
            "max_time": self.max_time,
            "last_world_year": self.last_world_year,
            "difference": difference,
        }


class OwidChartTemplateRecord(db.Model):
    """Represents the owid_charts_templates database view."""

    __tablename__ = "owid_charts_templates"

    chart_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(primary_key=True)
    template_title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

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


__all__ = [
    "TemplateNeedUpdateRecord",
    "OwidChartTemplateRecord",
]
