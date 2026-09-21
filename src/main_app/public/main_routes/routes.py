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
from flask.views import MethodView
from flask.wrappers import Response

from ...jobs_workers.public_jobs_workers.copy_svg_langs import (
    setup_svg_langs_form,
)

logger = logging.getLogger(__name__)


class IndexView(MethodView):
    """View to handle requests for the main application landing page."""

    def get(self) -> str:
        """Render index page with SVG language setup form."""
        form = setup_svg_langs_form()

        return render_template(
            "index.html",
            form=form,
        )


class FaviconView(MethodView):
    """View to serve the application favicon."""

    def get(self) -> Response:
        """Serve the favicon icon from the static assets directory."""
        return send_from_directory(
            current_app.static_folder,
            "favicon.ico",
            mimetype="image/x-icon",
        )


class MainView:
    """Registrar class to bind main MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register main URL rules on the provided blueprint."""
        bp.add_url_rule("/", view_func=IndexView.as_view("index"))
        bp.add_url_rule("/favicon.ico", view_func=FaviconView.as_view("favicon"))


__all__ = [
    "IndexView",
    "FaviconView",
    "MainView",
]
