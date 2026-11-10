"""
Flask application factory.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from flask import request

logger = logging.getLogger(__name__)


def _format_timestamp(
    value: str | datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    default: str = "",
) -> str:
    """Format a timestamp string or datetime/date object using the specified format string."""
    if not value:
        return default

    if not format_str:
        format_str = "%Y-%m-%d %H:%M:%S"

    if isinstance(value, datetime) or hasattr(value, "strftime"):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            logger.exception("Failed to parse timestamp: %s", value)
            logger.error("type of value: %s", type(value))
            return default

    return dt.strftime(format_str)  # type: ignore


def format_long_date(value: str | datetime, default: str = "") -> str:
    """Format ISO8601 like '2026-05-28T23:51:50' to '2026-05-28 23:51:50'."""
    return _format_timestamp(
        value=value,
        format_str="%Y-%m-%d %H:%M:%S",
        default=default,
    )


def format_date(value: str | datetime, format_str: str = "%Y-%m-%d %H:%M:%S", default: str = "") -> str:
    """Format ISO8601 like '2026-05-28T23:51:50' to '2026-05-28 23:51:50'."""
    return _format_timestamp(
        value=value,
        format_str=format_str,
        default=default,
    )


def format_short_date(value: str | datetime, default: str = "") -> str:
    """Format ISO8601 like '2026-05-28T23:51:50' to '23:51:50"""
    return _format_timestamp(
        value=value,
        format_str="%H:%M:%S",
        default=default,
    )


def get_status_class(status: str) -> str:
    status_classes = {
        "running": "primary",
        "imported": "success",
        "imported_fallback": "success",
        "completed": "success",
        "changed": "success",
        "missing": "warning",
        "skipped": "warning",
        "cancelled": "warning",
        "failed": "danger",
        "error": "danger",
        "errors": "danger",
        "pending": "secondary",
    }
    return status_classes.get(str(status).lower(), "secondary")


def short_url(value: str) -> str:
    """Extract the last segment of a URL path.

    For example, 'https://commons.wikimedia.org/wiki/File:Example.svg?test'
    becomes 'File:Example.svg'.

    Args:
        value: A URL string.

    Returns:
        The last segment of the URL path, or empty string if parsing fails.
    """
    if not value or not isinstance(value, str):
        return ""
    url = ""
    try:
        # Remove trailing slash, split by '/', take last segment
        url = value.rstrip("/").rsplit("/", 1)[-1]
    except Exception:
        logger.exception("Failed to extract short URL from: %s", value)

    # Remove query string
    url = url.split("?")[0].strip()
    return url


def check_active_route(route_name: str) -> str:
    route_name = route_name.replace("%20", " ")
    if route_name == request.path:
        return "active fw-bold"
    return ""


def commas_filter(value: str) -> str:
    try:
        return f"{value:,}"
    except (ValueError, TypeError):
        return value


def to_json_filter(value: object, indent: int = 2) -> str:
    """Serialize a value for template display.
    Args:
        value: Value to serialize.
        indent: JSON indentation width.
    Returns:
        UTF-8-preserving JSON text.
    """
    return json.dumps(value, ensure_ascii=False, indent=indent)


def is_job_running(job_status: str | None) -> bool:
    if not job_status:
        return False
    return job_status.lower() in ["pending", "running"]


filters = {
    "format_long_date": format_long_date,
    "format_short_date": format_short_date,
    "format_date": format_date,
    "get_status_class": get_status_class,
    "short_url": short_url,
    "check_active_route": check_active_route,
    "is_job_running": is_job_running,
    "commas": commas_filter,
    "to_json": to_json_filter,
}

__all__ = [
    "filters",
]
