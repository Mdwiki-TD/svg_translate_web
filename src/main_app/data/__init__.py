"""

"""

from __future__ import annotations
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

json_files = Path(__file__).parent.glob('*.json')

data_list = {}

for file in json_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data_list[file.stem] = json.load(f)
    except Exception as e:
        logger.error(f'Error loading data from {file}: {e}')


def get_slug_categories(slug: str) -> list[str]:
    topics = data_list.get("templates_slugs_topics", {}).get(slug)
    if not topics:
        logger.warning(f'No topics found for slug {slug}')
        return []

    topics_categories = data_list.get("topics_categories", {})

    result = []

    for x in topics:
        result.extend(topics_categories.get(x, []))

    logger.debug(f'Found categories for slug {slug}: {result}')

    return result


__all__ = [
    "data_list",
    "get_slug_categories",
]
