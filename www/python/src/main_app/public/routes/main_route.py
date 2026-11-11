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
        """Serve the landing page."""
        form = setup_svg_langs_form()
        return render_template(
            "index.html",
            form=form,
        )


class FaviconView(MethodView):
    """View to serve the application favicon."""

    def get(self) -> Response:
        """Stream ``favicon.ico`` from the static folder."""
        return send_from_directory(
            current_app.static_folder,  # pyright: ignore[reportArgumentType]
            "favicon.ico",
            mimetype="image/x-icon",
        )


class MainHealthView(MethodView):
    """Health check endpoint for load balancers and monitoring."""

    def get(self) -> tuple[dict[str, str], int]:
        """Return health status."""
        return {"status": "ok"}, 200


class MainToolinfoView(MethodView):
    """Serve the Toolhub metadata file (toolinfo.json)."""

    def get(self) -> Response:
        """Stream ``toolinfo.json`` from the static folder."""
        return send_from_directory(
            current_app.static_folder,  # pyright: ignore[reportArgumentType]
            "toolinfo.json",
            mimetype="application/json",
        )


class MainView:
    """Registrar for the main application views."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register main URL rules on the provided blueprint."""
        bp.add_url_rule("/", view_func=IndexView.as_view("index"))
        bp.add_url_rule("/favicon.ico", view_func=FaviconView.as_view("favicon"))
        bp.add_url_rule("/healthz", view_func=MainHealthView.as_view("healthz"))
        bp.add_url_rule("/toolinfo.json", view_func=MainToolinfoView.as_view("toolinfo"))


__all__ = [
    "IndexView",
    "FaviconView",
    "MainView",
]
