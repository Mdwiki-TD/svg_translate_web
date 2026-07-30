from __future__ import annotations

import logging

from ...extensions import db
from ..models.views import TemplateNeedUpdateView

logger = logging.getLogger(__name__)


class ViewsService:
    def __init__(self) -> None:
        pass

    def list_templates_need_update(self) -> list[TemplateNeedUpdateView]:
        """Return all templates"""
        query = db.session.query(TemplateNeedUpdateView).order_by(TemplateNeedUpdateView.template_title)
        return query.all()


__all__ = [
    "ViewsService",
]
