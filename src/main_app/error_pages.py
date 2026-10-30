"""Flask error handlers plus no-cache headers for form-related routes."""

from __future__ import annotations

import logging
from urllib.parse import parse_qsl, urlencode

from flask import Flask, Response, flash, jsonify, render_template, request
from flask_wtf.csrf import CSRFError

from .database.services.error_log_service import ErrorLogService

logger = logging.getLogger(__name__)


# Paths that browsers/crawlers hit routinely; logging them is just noise
SKIP_ROUTES = (
    "/robots.txt",
    "/.well-known",
)

# Headers that may carry credentials or session data; never write them to logs
SENSITIVE_HEADERS = frozenset(
    {
        "cookie",
        "set-cookie",
        "authorization",
        "proxy-authorization",
        "x-csrf-token",
        "x-api-key",
    }
)

# Query parameters that may carry secrets (OAuth codes, tokens, ...)
SENSITIVE_QUERY_KEYS = frozenset(
    {
        "token",
        "access_token",
        "oauth_token",
        "oauth_verifier",
        "code",
        "state",
        "key",
        "password",
        "csrf_token",
    }
)

# Only headers useful for telling bots from real browsers are logged
USEFUL_HEADERS = (
    "User-Agent",
    "Accept",
    "Accept-Language",
    "Accept-Encoding",
    "Referer",
    "Sec-Fetch-Mode",
    "Sec-Fetch-Dest",
    "Sec-Ch-Ua",
    "X-Request-Id",
)

# Endpoint prefixes (blueprints) whose responses must never be cached
NO_CACHE_ENDPOINTS = ("auth.", "publish.", "fixrefs.", "cxtoken.")


def safe_headers(headers) -> dict[str, str]:
    """Return headers with sensitive values redacted."""
    return {k: ("[REDACTED]" if k.lower() in SENSITIVE_HEADERS else v) for k, v in headers.items()}


def safe_query() -> str:
    """Return the query string with secret-looking values redacted."""
    raw = request.query_string.decode("utf-8", errors="replace")
    pairs = parse_qsl(raw, keep_blank_values=True)
    return urlencode([(k, "[REDACTED]" if k.lower() in SENSITIVE_QUERY_KEYS else v) for k, v in pairs])


def client_ip() -> str:
    """Return the first X-Forwarded-For hop, falling back to the socket address."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "-"


def log_error(label: str, e: Exception, level: int = logging.ERROR) -> None:
    """Write a single-line, credential-free log entry for an HTTP error."""
    headers = safe_headers(request.headers)
    picked = {name: headers[name] for name in USEFUL_HEADERS if name in headers}

    # %r escapes newlines, so user-controlled values cannot forge extra log lines
    logger.log(
        level,
        "%s | path=%r | query=%r | method=%s | ip=%s | route=%s | has_cookie=%s | headers=%r | error=%s",
        label,
        request.path,
        safe_query(),
        request.method,
        client_ip(),
        list(request.access_route),
        "cookie" in request.headers,
        picked,
        e,
    )
    # Also persist to the database; the service never raises
    ErrorLogService().log_request(
        status_code=getattr(e, "code", None) or 500,
        error=e,
        query=safe_query(),
        ip=client_ip(),
    )


def wants_json() -> bool:
    """True when the client expects a JSON error body."""
    return request.is_json or request.path.startswith("/api/")


def respond(
    status: int,
    title: str,
    error: str,
    flash_message: str,
    json_message: str | None = None,
    category: str = "warning",
) -> tuple[str | Response, int]:
    """Build the JSON or HTML error response."""
    if wants_json():
        body = {"error": error}
        if json_message is not None:
            body["message"] = json_message
        return jsonify(body), status

    flash(flash_message, category)
    return render_template("error.html", title=title), status


def register_cache_headers(app: Flask) -> None:
    """Prevent CSRF token caching on form-related routes."""

    @app.after_request
    def add_cache_headers(response):
        if request.endpoint and request.endpoint.startswith(NO_CACHE_ENDPOINTS):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


def register_error_pages(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(e: Exception) -> tuple[str | Response, int]:
        """Handle 400 errors"""
        log_error("400 Bad request", e)
        return respond(400, "Bad Request", "Bad request", "Bad request", str(e))

    @app.errorhandler(401)
    def unauthorized(e: Exception) -> tuple[str | Response, int]:
        """Handle 401 errors"""
        log_error("401 Unauthorized", e, logging.WARNING)
        return respond(
            401,
            "Unauthorized",
            "Unauthorized",
            "Please log in to access this page",
            "Authentication required",
        )

    @app.errorhandler(403)
    def forbidden(e: Exception) -> tuple[str | Response, int]:
        """Handle 403 errors"""
        log_error("403 Forbidden", e)
        return respond(403, "Access Denied", "Forbidden", "Access denied", "Access denied", "danger")

    @app.errorhandler(404)
    def page_not_found(e: Exception) -> tuple[str | Response, int]:
        """Handle 404 errors"""
        if not request.path.startswith(SKIP_ROUTES):
            log_error("404 Not found", e)
        return respond(404, "Page Not Found", "Not found", "Page not found", str(e))

    @app.errorhandler(405)
    def method_not_allowed(e: Exception) -> tuple[str | Response, int]:
        """Handle 405 errors"""
        log_error("405 Method not allowed", e)
        return respond(405, "Method Not Allowed", "Method not allowed", "Method not allowed", str(e))

    @app.errorhandler(429)
    def too_many_requests(e: Exception) -> tuple[str | Response, int]:
        """Handle 429 rate limit errors"""
        log_error("429 Rate limit exceeded", e, logging.WARNING)
        return respond(
            429,
            "Rate Limit Exceeded",
            "Too many requests",
            "Too many requests. Please try again later.",
            "Rate limit exceeded",
        )

    @app.errorhandler(500)
    def internal_server_error(e: Exception) -> tuple[str | Response, int]:
        """Handle 500 errors"""
        log_error("500 Internal Server Error", e)
        return respond(500, "Internal Server Error", "Internal server error", "Internal Server Error", None, "danger")

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> tuple[str | Response, int]:
        """Handle CSRF token errors"""
        log_error("400 CSRF error", e)
        return respond(
            400,
            "Session Expired",
            "CSRF error",
            "Session expired or invalid. Please try again.",
            "Session expired or invalid",
        )


__all__ = [
    "register_error_pages",
    "register_cache_headers",
]
