from __future__ import annotations

import logging

from ...extensions import db
from ..models.views import OwidChartTemplateRecord, TemplateNeedUpdateRecord

logger = logging.getLogger(__name__)


# ── SELECT ───────────────────────────────────────────────


def list_templates_need_update() -> list[TemplateNeedUpdateRecord]:
    """Return all templates"""
    query = db.session.query(TemplateNeedUpdateRecord).order_by(TemplateNeedUpdateRecord.template_title)
    return query.all()


def list_owid_charts_templates() -> list[OwidChartTemplateRecord]:
    """Return all charts_templates"""
    query = db.session.query(OwidChartTemplateRecord).order_by(OwidChartTemplateRecord.template_title)
    return query.all()


class ViewsService:
    def __init__(self) -> None:
        pass

    def list_templates_need_update(self) -> list[TemplateNeedUpdateRecord]:
        return list_templates_need_update()

    def list_owid_charts_templates(self) -> list[OwidChartTemplateRecord]:
        return list_owid_charts_templates()


__all__ = [
    "ViewsService",
    "list_templates_need_update",
    "list_owid_charts_templates",
]
