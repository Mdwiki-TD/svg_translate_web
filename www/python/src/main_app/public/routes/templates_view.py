"""Public templates dashboard page."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)
from flask.views import MethodView

from ...database.services import (
    TemplateService,
)

logger = logging.getLogger(__name__)


class TemplatesView(MethodView):
    """View to render the public templates dashboard page."""

    def __init__(self) -> None:
        self.service = TemplateService()

    def get(self) -> str:
        """Render the templates dashboard page."""
        return render_template(
            "templates.html",
        )

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the templates dashboard route on the blueprint."""
        bp.add_url_rule("/", view_func=cls.as_view("dashboard"))


__all__ = [
    "TemplatesView",
]
