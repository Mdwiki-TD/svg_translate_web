"""
Utilities for inserting generated wikitext blocks before specific markers.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


def add_before(text: str, new_text: str, search_text: str) -> str:
    res = re.search(search_text, text, flags=re.IGNORECASE | re.MULTILINE)
    if res:
        start = res.start()
        text = text[:start].rstrip() + "\n" + new_text + "\n\n" + text[start:].lstrip()
    return text


def insert_before_methods(text, other_versions_text):
    # Try to add before the license header
    modified_text = add_before(text, other_versions_text, r"==\s*\{\{\s*int:license-header\s*\}\}\s*==")

    if modified_text == text:
        # Try to add before the first category
        modified_text = add_before(text, other_versions_text, r"\[\[\s*category:")
    return modified_text


__all__ = [
    "insert_before_methods",
]
