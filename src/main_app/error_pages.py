""" """

from __future__ import annotations

import logging

from flask import Flask, Response, flash, jsonify, render_template, request
from flask_wtf.csrf import CSRFError

logger = logging.getLogger(__name__)


def register_error_pages(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(e: Exception) -> tuple[str | Response, int]:
        """Handle 400 errors"""
        logger.error("Bad request: %s", e)
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Bad request", "message": str(e)}), 400

        flash("Bad request", "warning")
        return render_template("error.html", title="Bad Request"), 400

    @app.errorhandler(401)
    def unauthorized(e: Exception) -> tuple[str | Response, int]:
        """Handle 401 errors"""
        logger.warning("Unauthorized: %s", e)
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
        flash("Please log in to access this page", "warning")
        return render_template("error.html", title="Unauthorized"), 401

    @app.errorhandler(403)
    def forbidden(e: Exception) -> tuple[str | Response, int]:
        """Handle 403 errors"""
        logger.error("Forbidden access: %s", e)
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
        flash("Access denied", "danger")
        return render_template("error.html", title="Access Denied"), 403

    @app.errorhandler(404)
    def page_not_found(e: Exception) -> tuple[str | Response, int]:
        """Handle 404 errors"""
        # Skip logging for `/.well-known/` which is used in browser console
        skip_routs = (
            "/robots.txt",
            "/.well-known",
        )
        if not request.path.startswith(skip_routs):
            logger.error("%s Page not found: %s", request.path, e)

        # Return JSON response for API requests
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Not found", "message": str(e)}), 404
        flash("Page not found", "warning")

        # Return HTML response for web requests
        return render_template("error.html", title="Page Not Found"), 404

    @app.errorhandler(405)
    def method_not_allowed(e: Exception) -> tuple[str | Response, int]:
        """Handle 405 errors"""
        logger.error("Method not allowed: %s", e)
        flash("Method not allowed", "warning")
        return render_template("error.html", title="Method Not Allowed"), 405

    @app.errorhandler(429)
    def too_many_requests(e: Exception) -> tuple[str | Response, int]:
        """Handle 429 rate limit errors"""
        logger.warning("Rate limit exceeded: %s", e)
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Too many requests", "message": "Rate limit exceeded"}), 429
        flash("Too many requests. Please try again later.", "warning")
        return render_template("error.html", title="Rate Limit Exceeded"), 429

    @app.errorhandler(500)
    def internal_server_error(e: Exception) -> tuple[str | Response, int]:
        """Handle 500 errors"""
        logger.error("Internal Server Error: %s", e)
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        flash("Internal Server Error", "danger")
        return render_template("error.html", title="Internal Server Error"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> tuple[str | Response, int]:
        """Handle CSRF token errors"""
        logger.error("CSRF error: %s", e)
        flash("Session expired or invalid. Please try again.", "warning")
        return render_template("error.html", title="Session Expired"), 400


__all__ = [
    "register_error_pages",
]
