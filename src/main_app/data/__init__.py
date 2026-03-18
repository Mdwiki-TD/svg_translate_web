""" """

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path

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


def get_slug_categories(slug: str) -> list[str]:
    templates_slugs_topics = load_data("templates_slugs_topics")
    topics = templates_slugs_topics.get(slug)
    if not topics:
        logger.warning(f"No topics found for slug {slug}")
        return []

    topics_categories = load_data("topics_categories")

    result = []

    for x in topics:
        result.extend(topics_categories.get(x, []))

    logger.debug(f"Found categories for slug {slug}: {result}")

    return result


__all__ = [
    "get_slug_categories",
]
