"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    current_app,
    render_template,
    send_from_directory,
)
from werkzeug.wrappers.response import Response

from ...jobs_workers.public_jobs_workers.copy_svg_langs import setup_svg_langs_form

logger = logging.getLogger(__name__)


class MainRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(self.index)
        self.bp.get("/favicon.ico")(self.favicon)

    def index(self) -> str:
        form = setup_svg_langs_form()

        return render_template(
            "index.html",
            form=form,
        )

    def favicon(self) -> Response:
        return send_from_directory(current_app.static_folder, "favicon.ico", mimetype="image/x-icon")


__all__ = [
    "MainRoutes",
]
