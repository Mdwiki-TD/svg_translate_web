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

from .forms import CopySvgLangsForm

from ...db.services import SettingsService

logger = logging.getLogger(__name__)


class MainRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(self.index)
        self.bp.get("/favicon.ico")(self.favicon)

    def index(self) -> str:
        all_settings = SettingsService().get_all_settings_ready()
        form = CopySvgLangsForm()
        # set upload default dynamically only on GET (first load)
        upload_disabled_by_default = bool(
            all_settings and all_settings.get("copy_svg_langs_upload_disabled_by_default", False)
        )
        form.upload.data = not upload_disabled_by_default

        return render_template(
            "index.html",
            form=form,
        )

    def favicon(self) -> Response:
        return send_from_directory(current_app.static_folder, "favicon.ico", mimetype="image/x-icon")


__all__ = [
    "MainRoutes",
]
