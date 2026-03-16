"""

"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def format_stage_timestamp(value: str) -> str:
    """Format ISO8601 like '2025-10-27T04:41:07' to 'Oct 27, 2025, 4:41 AM'."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except Exception:
        logger.exception("Failed to parse timestamp: %s", value)
        return ""
    # convert 24h → 12h with AM/PM
    hour24 = dt.hour
    ampm = "AM" if hour24 < 12 else "PM"
    hour12 = hour24 % 12 or 12
    minute = f"{dt.minute:02d}"
    month = dt.strftime("%b")  # Oct
    return f"{month} {dt.day}, {dt.year}, {hour12}:{minute} {ampm}"


def short_url(value: str) -> str:
    """Extract the last segment of a URL path.

    For example, 'https://commons.wikimedia.org/wiki/File:Example.svg?test'
    becomes 'File:Example.svg'.

    Args:
        value: A URL string.

    Returns:
        The last segment of the URL path, or empty string if parsing fails.
    """
    if not value:
        return ""
    url = ""
    try:
        url = value.rstrip('/').rsplit('/', 1)[-1]
    except Exception:
        logger.exception("Failed to extract short URL from: %s", value)

    url = url.split("?")[0].strip()
    return url
