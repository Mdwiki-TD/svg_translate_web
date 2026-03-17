"""
Utilities for extracting and merging wikitext categories.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import wikitextparser as wtp
from wikitextparser import WikiLink

logger = logging.getLogger(__name__)


@dataclass
class CategoryLink:
    link: WikiLink
    target: str


def capitalize_category(str_category) -> str:
    """
    Capitalizes the first letter of each part in a category string separated by a colon.
    """

    def upper_first(s) -> str:
        """
        Capitalizes the first character of a string.
        """
        return f"{s[0].upper()}{s[1:]}" if len(s) > 1 else s.upper()

    # Check if the string contains a colon separator
    if ":" not in str_category:
        return str_category

    # Remove leading/trailing whitespace including special characters
    str_category = str_category.strip()

    # Split the string into two parts at the first colon occurrence
    namespace, name = str_category.split(":", 1)

    # Capitalize the first letter of each part
    namespace = upper_first(namespace)
    name = upper_first(name)

    return f"{namespace}:{name}"


def create_category_link_from_str(str_link: str) -> CategoryLink:
    """
    Create a CategoryLink object from a string representation of a wiki link.
    """
    link = WikiLink(str_link)

    # clean target
    target = link.target.strip().replace("_", " ")
    target = capitalize_category(target)

    return CategoryLink(link=link, target=target)


def extract_categories(wikitext: str) -> list[CategoryLink]:
    """
    Extracts category WikiLinks from the given wikitext.
    """
    # Parse the input wikitext using the wtp parser
    parsed = wtp.parse(wikitext)

    # Filter wikilinks to find those starting with "Category:"
    # Added .lower() to ensure case-insensitive matching (e.g., [[category:...]])
    return [
        create_category_link_from_str(wl.string)
        for wl in parsed.wikilinks
        if wl.target.strip().lower().startswith("category:")
    ]


def find_missing_categories(
    target_categories: list[CategoryLink],
    base_categories: list[CategoryLink],
) -> list[CategoryLink]:
    """
    Identifies WikiLinks in 'base_categories' that are missing from 'target_categories'.

    Comparison is case-insensitive.
    """
    # Return base_categories if there is nothing to compare against
    if not target_categories:
        return base_categories

    # Using a set for target_targets improves lookup performance to O(1)
    target_targets = {cat.target for cat in target_categories}

    # Return only the categories from base_categories that aren't already in target_categories
    return [cat for cat in base_categories if cat.target not in target_targets]


def merge_categories(old_text: str, new_text: str) -> str:
    """
    Appends categories found in old_text to new_text if they are not already present.
    """
    # Parse categories from both versions of the text
    old_cats = extract_categories(old_text)

    if not old_cats:
        return new_text

    new_cats = extract_categories(new_text)

    # Logic fix: We want to find categories in 'old_text' that are missing in 'new_text'
    missing_categories = find_missing_categories(
        target_categories=new_cats,  # The current set of categories
        base_categories=old_cats,  # The potential candidates to re-add
    )

    # If no missing categories are found, return the text as is
    if not missing_categories:
        return new_text

    # Convert the missing CategoryLink objects back to their string representation
    missing_categories_str = "\n".join([cat.link.string for cat in missing_categories])

    # Append the missing categories to the end of the new text
    return f"{new_text}\n{missing_categories_str}"


__all__ = [
    "merge_categories",
]
