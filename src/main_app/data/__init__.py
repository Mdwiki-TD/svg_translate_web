""" """

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1024)
def load_data(key):
    key = Path(key).name
    file_path = Path(__file__).parent / f"{key}.json"
    data = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading data from {key}: {e}")

    return data


def extract_slug_from_url(url: str) -> str:
    """
    Extracts the slug (path component) from a URL.

    Args:
        url: A URL string (e.g., "https://ourworldindata.org/grapher/unemployment-rate-estimates-modeled-vs-national")

    Returns:
        The slug part of the URL (e.g., "unemployment-rate-estimates-modeled-vs-national")

    Examples:
        >>> extract_slug_from_url("https://ourworldindata.org/grapher/unemployment-rate-estimates-modeled-vs-national")
        'unemployment-rate-estimates-modeled-vs-national'
        >>> extract_slug_from_url("https://example.com/path?query=1#fragment")
        'path'
    """
    if not url:
        return ""

    parsed = urlparse(url)
    path = parsed.path.strip("/")
    return path.split("/")[-1] if path else ""


def get_slug_categories(slug: str) -> list[str]:
    if not slug:
        return ""

    slug = extract_slug_from_url(slug)
    templates_slugs_topics = load_data("templates_slugs_topics")

    topics = templates_slugs_topics.get(slug)
    if not topics:
        logger.warning(f"No topics found for slug {slug}")
        return []

    topics_categories = load_data("topics_categories")

    result = []

    for x in topics:
        result.extend(topics_categories.get(x, []))

    result = list(set(result))

    logger.debug(f"Found categories for slug {slug}: {result}")

    return result


__all__ = [
    "get_slug_categories",
]
