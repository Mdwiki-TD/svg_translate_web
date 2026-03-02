"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


def addBefore(text: str, newText: str, searchText: str) -> str:
    res = re.search(searchText, text, flags=re.IGNORECASE | re.MULTILINE)
    if res:
        start = res.start()
        text = text[:start].rstrip() + "\n" + newText + "\n\n" + text[start:].lstrip()
    return text


def insert_before_methods(text, other_versions_text):
    # Try to add before the license header
    modified_text = addBefore(text, other_versions_text, r"==\s*\{\{\s*int:license-header\s*\}\}\s*==")

    if modified_text == text:
        # Try to add before the first category
        modified_text = addBefore(text, other_versions_text, r"\[\[\s*category:")
    return modified_text


__all__ = [
    "insert_before_methods",
]
