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
    def __init__(self) -> None:
        self.service = TemplateService()

    def register(self, bp: Blueprint) -> None:

        routes = [
            ("/", "GET", self.dashboard),
        ]
        for rule, method, target in routes:
            bp.route(rule, methods=[method])(target)

    def dashboard(self):
        return render_template(
            "templates.html",
        )


__all__ = [
    "TemplatesView",
]
