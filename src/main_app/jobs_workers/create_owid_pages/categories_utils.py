"""
"""

from __future__ import annotations

import logging
import wikitextparser as wtp
from wikitextparser import WikiLink

logger = logging.getLogger(__name__)


def extract_categories(wikitext: str) -> list[WikiLink]:
    """
    Extracts category WikiLinks from the given wikitext.
    """
    # Parse the input wikitext using the wtp parser
    parsed = wtp.parse(wikitext)

    # Filter wikilinks to find those starting with "Category:"
    # Added .lower() to ensure case-insensitive matching (e.g., [[category:...]])
    return [
        wl for wl in parsed.wikilinks
        if wl.target.strip().lower().startswith("category:")
    ]


def find_missing_categories(
    target_categories: list[WikiLink],
    base_categories: list[WikiLink],
) -> list[WikiLink]:
    """
    Identifies WikiLinks in 'target_categories' that are missing from 'base_categories'.
    """
    # Using a set for base_targets improves lookup performance to O(1)
    base_targets = {cat.target.strip() for cat in target_categories}

    # Return only the categories from target_categories that aren't already in base
    return [
        cat for cat in base_categories
        if cat.target.strip() not in base_targets
    ]


def merge_categories(old_text: str, new_text: str) -> str:
    """
    Appends categories found in old_text to new_text if they are not already present.
    """
    # Parse categories from both versions of the text
    old_cats = extract_categories(old_text)
    new_cats = extract_categories(new_text)

    # Logic fix: We want to find categories in 'old_text' that are missing in 'new_text'
    missing_categories = find_missing_categories(
        base_categories=new_cats,    # The current set of categories
        target_categories=old_cats,  # The potential candidates to re-add
    )

    # If no missing categories are found, return the text as is
    if not missing_categories:
        return new_text

    # Convert the missing WikiLink objects back to their string representation
    missing_categories_str = "\n".join([cat.string for cat in missing_categories])

    # Append the missing categories to the end of the new text
    return f"{new_text}\n{missing_categories_str}"


__all__ = [
    "merge_categories",
]
