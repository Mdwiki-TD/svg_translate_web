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

bp_main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@bp_main.get("/")
def index():

    return render_template(
        "index.html",
        form={},
        set_titles_limit=False,
    )


@bp_main.get("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")


__all__ = ["bp_main"]
