"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from ...db import check_connection_health, log_all_pool_status
from ...routes_utils import get_error_message
from ...users.current import current_user

bp_main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@bp_main.get("/")
def index():
    current_user_obj = current_user()
    error_message = get_error_message(request.args.get("error"))
    if error_message:
        logger.warning(f"Error message: {error_message}")
        flash(error_message, "warning")

    return render_template(
        "index.html",
        form={},
        set_titles_limit=False,
        current_user=current_user_obj,
    )


@bp_main.get("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")


@bp_main.get("/health")
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "svg-translate-web",
    }), 200


@bp_main.get("/health/db")
def db_health_check():
    """Database connectivity and pool health check."""
    # Log pool status for monitoring
    log_all_pool_status(force=True)

    # Check HTTP engine health
    http_health = check_connection_health()

    if http_health["status"] != "healthy":
        return jsonify({
            "status": "unhealthy",
            "http_pool": http_health,
        }), 503

    return jsonify({
        "status": "healthy",
        "http_pool": http_health.get("pool", {}),
    }), 200


__all__ = ["bp_main"]
