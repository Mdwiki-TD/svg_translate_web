"""
"""

from __future__ import annotations

import logging
import wikitextparser as wtp
from wikitextparser import WikiLink

logger = logging.getLogger(__name__)


def _extract_categories(wikitext: str) -> list[WikiLink]:
    """
    Extract category names from wikitext.
    """
    # Parse the input wikitext using the wtp parser
    parsed = wtp.parse(wikitext)
    # Initialize an empty list to store category WikiLinks
    cats = []
    # Iterate through all wikilinks found in the parsed text
    for wl in parsed.wikilinks:
        # Remove any leading or trailing whitespace from the target
        target = wl.target.strip()
        # Check if the target starts with "Category:" to identify categories
        if target.startswith("Category:"):
            # Add valid category WikiLinks to our list
            cats.append(wl)

    # Return the list of extracted categories
    return cats


def extract_categories_list(
    base_categories: list[WikiLink],
    target_categories: list[WikiLink],
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
    Extends the categories in new_text by combining with categories from old_text.
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
