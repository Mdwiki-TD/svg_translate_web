"""
Insert generated wikitext blocks before specific markers.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class BeforeMarkerInserter:
    """Inserts a block of wikitext before a marker found in the page."""

    LICENSE_HEADER_PATTERN = r"==\s*\{\{\s*int:license-header\s*\}\}\s*=="
    CATEGORY_PATTERN = r"\[\[\s*category:"

    def add_before(self, text: str, new_text: str, search_text: str) -> str:
        """Insert ``new_text`` before the first match of ``search_text``."""
        res = re.search(search_text, text, flags=re.I | re.M)
        if res:
            start = res.start()
            text = text[:start].rstrip() + "\n" + new_text + "\n\n" + text[start:].lstrip()
        return text

    def insert_before_methods(self, text: str, other_versions_text: str) -> str:
        """Insert before the license header, or before the first category."""
        modified_text = self.add_before(text, other_versions_text, self.LICENSE_HEADER_PATTERN)

        if modified_text == text:
            modified_text = self.add_before(text, other_versions_text, self.CATEGORY_PATTERN)
        return modified_text


__all__ = [
    "BeforeMarkerInserter",
]
