"""
"""

from __future__ import annotations

import logging
import wikitextparser as wtp
from wikitextparser import WikiLink

logger = logging.getLogger(__name__)


def _extract_categories(wikitext: str) -> list[WikiLink]:
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


def extract_categories_list(
    target_categories: list[WikiLink],
    base_categories: list[WikiLink],
) -> list[WikiLink]:
    """
    Identifies WikiLinks in 'target_categories' that are missing from 'base_categories'.
    """
    # Create a list of stripped target strings from new_categories for comparison
    target_categories = [
        x.target.strip()
        for x in target_categories
    ]

    # Filter new_categories to include only those not present in old_categories
    categories = [
        x for x in base_categories
        if x.target.strip() not in target_categories
    ]

    return categories


def extend_categories(old_text: str, new_text: str) -> str:
    """
    Appends categories found in old_text to new_text if they are not already present.
    """

    # Extract and merge categories from both old and new text
    categories = extract_categories_list(
        _extract_categories(old_text),
        _extract_categories(new_text),
    )
    # End of category extraction and merging

    # Convert the extracted category objects to strings and join with newlines
    new_categories = "\n".join([x.string for x in categories])
    # End of category string conversion
    # Append the combined categories to the new text with a newline separator
    new_text += f"\n{new_categories}"

    # End of text appending
    return new_text
