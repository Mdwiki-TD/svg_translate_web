"""Rate limiting for authentication endpoints, built on Flask-Limiter."""

from __future__ import annotations

import logging

from flask import Flask, Response, jsonify, request
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

LOGIN_LIMIT_STRATEGY = "5 per minute"
CALLBACK_LIMIT_STRATEGY = "10 per minute"

# Storage and header behavior come from the Flask config, e.g.:
#   RATELIMIT_STORAGE_URI = "redis://localhost:6379"  (default: "memory://")
#   RATELIMIT_HEADERS_ENABLED = True                  (adds Retry-After etc.)
limiter = Limiter(key_func=get_remote_address)

# Reusable decorators; apply them to views or put them in MethodView.decorators.
login_limit = limiter.limit(LOGIN_LIMIT_STRATEGY)
callback_limit = limiter.limit(CALLBACK_LIMIT_STRATEGY)


def _handle_rate_limit_exceeded(error: RateLimitExceeded) -> tuple[Response, int]:
    """Log the throttled request and return a JSON 429 response."""
    logger.warning(
        "Rate limit exceeded for key: %s (endpoint=%s, limit=%s)",
        get_remote_address(),
        request.endpoint,
        error.description,
    )
    return jsonify(error="Too many requests", limit=error.description), 429


def init_rate_limiter(app: Flask) -> None:
    """Attach the limiter and the 429 handler to the app.

    When running behind a trusted reverse proxy, wrap the app with werkzeug's
    ProxyFix first so remote_addr reflects the real client IP.
    """
    limiter.init_app(app)
    app.register_error_handler(RateLimitExceeded, _handle_rate_limit_exceeded)


__all__ = [
    "init_rate_limiter",
    "callback_limit",
    "login_limit",
]
