from __future__ import annotations

import logging
from typing import List

from ..engine import get_session
from ..models.views import TemplateNeedUpdateRecord

logger = logging.getLogger(__name__)


def list_templates_need_update() -> List[TemplateNeedUpdateRecord]:
    """Return all templates"""
    with get_session() as session:
        query = session.query(TemplateNeedUpdateRecord).order_by(TemplateNeedUpdateRecord.template_title)
        return query.all()


__all__ = [
    "list_templates_need_update",
]
