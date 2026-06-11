from __future__ import annotations

import logging
from typing import List

from ...extensions import db
from ..models.views import TemplateNeedUpdateRecord

logger = logging.getLogger(__name__)


# ── SELECT ───────────────────────────────────────────────


def list_templates_need_update() -> List[TemplateNeedUpdateRecord]:
    """Return all templates"""
    query = db.session.query(TemplateNeedUpdateRecord).order_by(TemplateNeedUpdateRecord.template_title)
    return query.all()


__all__ = [
    "list_templates_need_update",
]
