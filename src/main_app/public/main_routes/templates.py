""" """

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)
from ...database.services import (
    TemplateService,
)

logger = logging.getLogger(__name__)

class TemplatesView:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.service = TemplateService()
        self._setup_routes()

    def _setup_routes(self) -> None:

        routes = [
            ("/", "GET", self.dashboard),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

    def dashboard(self):
        return render_template(
            "templates.html",
        )

__all__ = [
    "TemplatesView",
]
