from __future__ import annotations

import logging

from ...extensions import db
from ..models.views import OwidChartTemplateView, TemplateNeedUpdateView

logger = logging.getLogger(__name__)


# ── SELECT ───────────────────────────────────────────────


def list_templates_need_update() -> list[TemplateNeedUpdateView]:
    """Return all templates"""
    query = db.session.query(TemplateNeedUpdateView).order_by(TemplateNeedUpdateView.template_title)
    return query.all()


def list_owid_charts_templates() -> list[OwidChartTemplateView]:
    """Return all charts_templates"""
    query = db.session.query(OwidChartTemplateView).order_by(OwidChartTemplateView.template_title)
    return query.all()


class ViewsService:
    def __init__(self) -> None:
        pass

    def list_templates_need_update(self) -> list[TemplateNeedUpdateView]:
        return list_templates_need_update()

    def list_owid_charts_templates(self) -> list[OwidChartTemplateView]:
        return list_owid_charts_templates()


__all__ = [
    "ViewsService",
    "list_templates_need_update",
    "list_owid_charts_templates",
]
