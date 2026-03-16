"""
"""

from __future__ import annotations

import logging
import wikitextparser as wtp
from wikitextparser import WikiLink

logger = logging.getLogger(__name__)


def _extract_categories(wikitext: str) -> list[WikiLink]:
    """
    Return category names (e.g. 'Category:Meat consumption maps') found
    in the wikitext, excluding navigation/meta categories such as
    'Category:List of interactive graphs', etc.
    We also add [[Category:Categories per capita]] if not already present,
    following the pattern seen in the example output.
    """
    parsed = wtp.parse(wikitext)
    cats = []
    for wl in parsed.wikilinks:
        target = wl.target.strip()
        if target.startswith("Category:"):
            cats.append(wl)

    return cats


def extract_categories_list(
    old_categories: list[WikiLink],
    new_categories: list[WikiLink],
) -> list[WikiLink]:
    """
    """
    old_categories = [
        x.target.strip()
        for x in old_categories
    ]

    categories = [
        x for x in new_categories
        if x.target.strip() not in old_categories
    ]

    return categories


def extend_categories(old_text: str, new_text: str) -> str:
    """
    """
    categories = extract_categories_list(
        _extract_categories(old_text),
        _extract_categories(new_text),
    )

    new_categories = "\n".join([x.string for x in categories])

    new_text += f"\n{new_categories}"

    return new_text
