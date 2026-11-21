from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..db_base import db
from ..models.views import TemplateNeedUpdateView

logger = logging.getLogger(__name__)


class ViewsService:
    def __init__(self, session: Session | None = None) -> None:
        self.session = session or db.session

    def list_templates_need_update(self) -> list[TemplateNeedUpdateView]:
        """Return all templates"""
        query = self.session.query(TemplateNeedUpdateView).order_by(TemplateNeedUpdateView.template_title)
        return query.all()


__all__ = [
    "ViewsService",
]
