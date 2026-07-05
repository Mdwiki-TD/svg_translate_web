"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    send_from_directory,
)
from werkzeug.wrappers.response import Response

logger = logging.getLogger(__name__)


class MainRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        def index() -> str:
            return render_template(
                "index.html",
                form={},
                set_titles_limit=False,
            )

        @self.bp.get("/favicon.ico")
        def favicon() -> Response:
            return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")


__all__ = [
    "MainRoutes",
]
