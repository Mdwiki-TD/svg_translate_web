# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- match_main_title_from_url
"""

import pytest

from src.main_app.utils.wikitext.titles_utils.main_file import match_main_title_from_url, match_main_title_from_url_new

# ---------- Tests for match_main_title_from_url ----------


tests_list = [
    # Basic valid line
    (
        "*'''Translate''': https://svgtranslate.toolforge.org/File:health-expenditure-government-expenditure,World,2000.svg",
        "File:health-expenditure-government-expenditure,World,2000.svg",
    ),
    # Extra spaces
    (
        "*'''Translate''':   https://svgtranslate.toolforge.org/File:Title-With_underscores-and,Stuff,2024(1).svg",
        "File:Title-With_underscores-and,Stuff,2024(1).svg",
    ),
    # Invalid domain
    (
        "*'''Translate''': https://example.org/File:bad.svg",
        None,
    ),
    # Wrong prefix
    (
        "Translate: https://svgtranslate.toolforge.org/File:miss.svg",
        None,
    ),
    # Not at line start
    (
        "  *'''Translate''': https://svgtranslate.toolforge.org/File:indented.svg",
        None,  # pattern anchors to start-of-line ^
    ),
]


@pytest.mark.parametrize(
    "line,expected",
    tests_list,
)
def test_match_main_title_from_url_various(line, expected):
    """Validate regex-based extraction from 'Translate' line."""
    assert match_main_title_from_url(line) == expected


@pytest.mark.parametrize(
    "line,expected",
    tests_list,
)
def test_match_main_title_from_url_new_various(line, expected):
    """Validate regex-based extraction from 'Translate' line."""
    assert match_main_title_from_url_new(line) == expected
