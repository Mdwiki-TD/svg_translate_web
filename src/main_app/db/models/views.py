from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db

logger = logging.getLogger(__name__)


class TemplateNeedUpdateView(db.Model):
    """ """

    __tablename__ = "templates_need_update"

    template_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    owid_variable_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_world_year: Mapped[int | None] = mapped_column(nullable=True)
    max_time: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (
        # Prevent SQLAlchemy from trying to create this as a table
        {
            "info": {
                "is_view": True,
                "replace_the_view": True,
                "create_query": """
                    CREATE OR REPLACE VIEW
                        templates_need_update AS
                    select
                        t.id AS template_id,
                        t.title AS template_title,
                        t.slug AS slug,
                        c.owid_variable_id AS owid_variable_id,
                        c.max_time AS max_time,
                        t.last_world_year AS last_world_year
                    from
                        owid_charts c
                        join templates t on t.slug = c.slug
                    where
                        t.last_world_year < c.max_time
                        AND c.max_time <= YEAR(now())
                        and t.last_world_year is not null
                        and c.status_404 is null
                    ;
                    """,
            }
        },
    )

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        difference = 0
        if self.max_time and self.last_world_year:
            difference = (self.max_time or 0) - (self.last_world_year or 0)
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "slug": self.slug,
            "owid_variable_id": self.owid_variable_id or "",
            "max_time": self.max_time,
            "last_world_year": self.last_world_year,
            "difference": difference,
        }


class OwidChartTemplateView(db.Model):  # type: ignore
    """
    Represents a database view joining charts and templates.
    Handles extended template metadata and manual runtime overrides.
    """

    __tablename__ = "owid_charts_templates"

    chart_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    template_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        # Prevent SQLAlchemy from trying to create this as a table
        {
            "info": {
                "is_view": True,
                "replace_the_view": True,
                "create_query": """
                    CREATE OR REPLACE VIEW
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

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "template_id": self.template_id,
            "template_title": self.template_title,
        }


__all__ = [
    "TemplateNeedUpdateView",
    "OwidChartTemplateView",
]
