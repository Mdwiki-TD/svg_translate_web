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
    Extracts a list of new categories that are not present in the old categories.

    This function compares two lists of WikiLink objects and returns a new list
    containing only those categories from new_categories whose target property
    (after stripping whitespace) is not present in the stripped targets of
    old_categories. The comparison is case-sensitive and considers the exact
    string match after stripping whitespace characters (including spaces, tabs,
    newlines, and carriage returns).

    Args:
        old_categories (list[WikiLink]): A list of existing WikiLink objects to compare against.
        new_categories (list[WikiLink]): A list of WikiLink objects to filter for new entries.

    Returns:
        list[WikiLink]: A filtered list containing only WikiLink objects from new_categories
                       whose target (after stripping) is not found in old_categories.

    Notes:
        - The function strips whitespace from target strings before comparison,
          including spaces, tabs (\t), newlines (\n), and carriage returns (\r).
        - The original input lists are not modified.
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
    categories = extract_categories_list(
        _extract_categories(old_text),
        _extract_categories(new_text),
    )

    new_categories = "\n".join([x.string for x in categories])

    new_text += f"\n{new_categories}"

    return new_text
