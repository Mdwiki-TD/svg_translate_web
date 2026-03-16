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

    Args:
        wikitext (str): The wikitext to parse. May contain special characters:
            - '\t' (tab)
            - '\r' (carriage return)
            - '\n' (newline)
            These are handled by the parser automatically.

    Returns:
        list[WikiLink]: A list of WikiLink objects representing categories found in the wikitext.
            Excludes navigation/meta categories like 'Category:List of interactive graphs'.
            Automatically adds 'Category:Categories per capita' if not already present.

    Notes:
        - Only categories starting with "Category:" are included
        - The function uses the wtp.parse() method to process the wikitext
        - Category targets are stripped of leading/trailing whitespace
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

    This function extracts categories from both old_text and new_text, merges them,
    and appends the combined categories to new_text.

    Args:
        old_text (str): The original text containing categories to be extracted.
        new_text (str): The new text to which the combined categories will be appended.

    Returns:
        str: The new_text with the combined categories appended at the end.

    Note:
        The categories are extracted using internal functions _extract_categories()
        and extract_categories_list(). The final categories are joined with newline
        characters and appended to new_text.
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
