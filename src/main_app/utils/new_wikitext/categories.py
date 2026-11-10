"""
Extract, merge and sort wikitext categories.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import wikitextparser as wtp
from wikitextparser import WikiLink

logger = logging.getLogger(__name__)


@dataclass
class CategoryLink:
    link: WikiLink
    target: str


class CategoryExtractor:
    """Reads category links from wikitext and normalizes their targets."""

    def capitalize_category(self, str_category) -> str:
        """Capitalize the first letter of each part of a ``Namespace:Name`` string."""

        def upper_first(s) -> str:
            return f"{s[0].upper()}{s[1:]}" if len(s) > 1 else s.upper()

        # Check if the string contains a colon separator
        if ":" not in str_category:
            return str_category

        # Remove leading/trailing whitespace including special characters
        str_category = str_category.strip()

        # Split the string into two parts at the first colon occurrence
        namespace, name = str_category.split(":", 1)

        return f"{upper_first(namespace)}:{upper_first(name)}"

    def create_category_link_from_str(self, str_link: str) -> CategoryLink:
        """Create a ``CategoryLink`` from a wiki link string."""
        link = WikiLink(str_link)

        # clean target
        target = link.target.strip().replace("_", " ").split("#")[0]
        target = self.capitalize_category(target)

        return CategoryLink(link=link, target=target)

    def extract_categories(self, wikitext: str) -> list[CategoryLink]:
        """Extract category wikilinks from the given wikitext."""
        if not isinstance(wikitext, str):
            return []
        parsed = wtp.parse(wikitext)

        # Case-insensitive match (e.g. [[category:...]])
        return [
            self.create_category_link_from_str(wl.string)
            for wl in parsed.wikilinks
            if wl.target.strip().lower().startswith("category:")
        ]


class CategoryMerger:
    """Merges categories between two texts and sorts categories."""

    def __init__(self, extractor: CategoryExtractor | None = None) -> None:
        self.extractor = extractor or CategoryExtractor()

    def find_missing_categories(
        self,
        target_categories: list[CategoryLink],
        base_categories: list[CategoryLink],
    ) -> list[CategoryLink]:
        """Return the categories of ``base_categories`` that are missing from ``target_categories``."""
        # Return base_categories if there is nothing to compare against
        if not target_categories:
            return base_categories

        target_targets = {cat.target for cat in target_categories}
        return [cat for cat in base_categories if cat.target not in target_targets]

    def merge_categories(self, old_text: str, new_text: str) -> str:
        """Append categories found in ``old_text`` to ``new_text`` if they are not already present."""
        if not new_text or not old_text:
            return new_text

        old_cats = self.extractor.extract_categories(old_text)

        if not old_cats:
            # TODO: we should insert the new categories to the text
            return new_text

        new_cats = self.extractor.extract_categories(new_text)

        missing_categories = self.find_missing_categories(
            target_categories=new_cats,
            base_categories=old_cats,
        )

        if not missing_categories:
            return new_text

        missing_categories_str = "\n".join([cat.link.string for cat in missing_categories])
        return f"{new_text}\n{missing_categories_str}"

    def sort_categories(self, wikitext: str) -> str:
        """Move all categories to the end of the text, sorted."""
        parsed = wtp.parse(wikitext)

        categories: list[Any] = []
        for wl in parsed.wikilinks:
            if wl.target.strip().lower().startswith("category:"):
                categories.append(wl.string)
                wl.string = ""

        if not categories:
            return wikitext

        new_wikitext = parsed.string.strip() + "\n"

        categories.sort()

        for x in categories:
            new_wikitext += f"\n{x}"

        return new_wikitext

    def get_missing_categories_list(self, cats_list: list[str], text: str) -> list[str]:
        """Return the links from ``cats_list`` that are not present in ``text``."""
        if not text:
            return []

        old_cats = self.extractor.extract_categories(text)

        if not old_cats:
            return [f"[[{cat_str}]]" for cat_str in cats_list]

        new_cats = [self.extractor.create_category_link_from_str(f"[[{cat_str}]]") for cat_str in cats_list]

        target_targets = {cat.target for cat in old_cats}
        missing_categories = [cat for cat in new_cats if cat.target not in target_targets]

        if not missing_categories:
            return []

        return [cat.link.string for cat in missing_categories]

    def merge_categories_into_text(self, cats_list: list[str], text: str) -> str:
        """Append the categories of ``cats_list`` missing from ``text`` to its end."""
        missing_categories_list = self.get_missing_categories_list(cats_list, text)

        if not missing_categories_list:
            return text

        missing_categories_str = "\n".join(missing_categories_list)
        return f"{text}\n{missing_categories_str}"


__all__ = [
    "CategoryExtractor",
    "CategoryLink",
    "CategoryMerger",
]
