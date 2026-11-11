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

# The limiter is a module-level singleton shared by every app created in the
# process, so response headers (X-RateLimit-*, Retry-After) are enabled here
# instead of through RATELIMIT_HEADERS_ENABLED. That way the behavior does not
# depend on which app was initialised first. Storage still comes from the Flask
# config: RATELIMIT_STORAGE_URI (default "memory://").
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

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
