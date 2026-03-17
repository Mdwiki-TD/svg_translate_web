"""
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import wikitextparser as wtp
from wikitextparser import WikiLink

logger = logging.getLogger(__name__)


@dataclass
class CategoryLink:
    link: WikiLink
    target: str


def capitalize_category(str_category):
    """
    """
    def upper_first(s) -> str:
        return f"{s[0].upper()}{s[1:]}" if len(s) > 1 else s.upper()

    if ":" not in str_category:
        return str_category

    str_category = str_category.strip()
    part_1, part_2 = str_category.split(":", 1)

    part_1 = upper_first(part_1)
    part_2 = upper_first(part_2)

    return f"{part_1}:{part_2}"


def create_category_link_from_str(str_link: str) -> CategoryLink:
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
        create_category_link_from_str(wl.string) for wl in parsed.wikilinks
        if wl.target.strip().lower().startswith("category:")
    ]


def find_missing_categories(
    target_categories: list[CategoryLink],
    base_categories: list[CategoryLink],
) -> list[CategoryLink]:
    """
    Identifies WikiLinks in 'target_categories' that are missing from 'base_categories'.
    """
    # Return base_categories if there is nothing to compare against
    if not target_categories:
        return base_categories

    # Using a set for base_targets improves lookup performance to O(1)
    base_targets = {
        cat.target
        for cat in target_categories
    }

    # Return only the categories from target_categories that aren't already in base
    return [
        cat for cat in base_categories
        if cat.target not in base_targets
    ]


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
        target_categories=new_cats,    # The current set of categories
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
