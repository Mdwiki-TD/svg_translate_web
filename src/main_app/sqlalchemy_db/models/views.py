from __future__ import annotations

import logging

from sqlalchemy import Column, Integer, String

from ..engine import BaseDb

logger = logging.getLogger(__name__)


class TemplateNeedUpdateRecord(BaseDb):
    """ """

    __tablename__ = "templates_need_update"

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_title = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), nullable=False, server_default="")
    last_world_year = Column(Integer, nullable=True)
    max_time = Column(Integer, nullable=True)

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


class OwidChartTemplateRecord(BaseDb):
    """ """

    __tablename__ = "owid_charts_templates"

    chart_id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_title = Column(String(255), unique=True, nullable=False)

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
