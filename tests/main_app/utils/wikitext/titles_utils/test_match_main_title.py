# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- match_main_title_from_url

Assumes the functions are available from the target module.
Replace `from your_module import ...` with your actual module name.
"""

import pytest

from src.main_app.utils.wikitext.titles_utils.main_file import (
    find_main_title_from_owidslidersrcs,
    match_main_title_from_url,
    match_main_title_from_url_new,
)

# ---------- Fixtures with realistic wikitext samples ----------


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


def test_find_main_title_from_owidslidersrcs():
    """Validate extraction of main title from {{owidslidersrcs}} template."""
    text = """
*'''Source''': https://ourworldindata.org/grapher/youth-mortality-rate
{{-}}

==Data==
{{owidslidersrcs|id=gallery|widths=240|heights=240
|gallery-World=
File:youth mortality rate, World, 1950.svg!year=1950
File:youth mortality rate, World, 1951.svg!year=1951
File:youth mortality rate, World, 1952.svg!year=1952
File:youth mortality rate, World, 1953.svg!year=1953
}}"""
    expected = "File:youth mortality rate, World, 1950.svg"
    assert find_main_title_from_owidslidersrcs(text) == expected


class TestFindMainTitleFromOwidslidersrcs:
    """Tests for the find_main_title_from_owidslidersrcs function."""

    def test_extract_from_gallery_world(self) -> None:
        """Test extracting title from gallery-World argument."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:test, World, 2020.svg!year=2020
        }}
        """
        result = find_main_title_from_owidslidersrcs(text)
        assert result == "test, World, 2020.svg"

    def test_extract_first_file_only(self) -> None:
        """Test that only the first file is extracted."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:first.svg!year=2020
        File:second.svg!year=2021
        }}
        """
        result = find_main_title_from_owidslidersrcs(text)
        assert result == "first.svg"

    def test_underscores_converted_to_spaces(self) -> None:
        """Test that underscores are converted to spaces."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:test_file.svg!year=2020
        }}
        """
        result = find_main_title_from_owidslidersrcs(text)
        assert result == "test file.svg"

    def test_no_owidslidersrcs_template(self) -> None:
        """Test when no {{owidslidersrcs}} template exists."""
        text = "Some text without the template"
        result = find_main_title_from_owidslidersrcs(text)
        assert result is None

    def test_no_gallery_world_argument(self) -> None:
        """Test when gallery-World argument is missing."""
        text = """
        {{owidslidersrcs|gallery-AllCountries=
        File:test.svg!country=XX
        }}
        """
        result = find_main_title_from_owidslidersrcs(text)
        assert result is None

    def test_case_insensitive_template_name(self) -> None:
        """Test that template name matching is case-insensitive."""
        text = """
        {{OWIDSLIDERSRCS|gallery-World=
        File:test.svg!year=2020
        }}
        """
        result = find_main_title_from_owidslidersrcs(text)
        assert result == "test.svg"

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = find_main_title_from_owidslidersrcs("")
        assert result is None
