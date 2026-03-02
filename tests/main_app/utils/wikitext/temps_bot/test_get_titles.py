# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- get_titles

"""

import pytest

from src.main_app.utils.wikitext.temps_bot import get_titles

# ---------- Tests for get_titles ----------


def test_get_titles_from_sample_prompt(sample_from_prompt):
    """Extract all .svg filenames from owidslidersrcs and ignore everything else."""
    titles = get_titles(sample_from_prompt)
    # All must end with .svg and contain expected country codes as part of filename
    assert all(t.endswith(".svg") for t in titles)
    # Check some expected members (whitespace around commas should have been stripped)
    assert "health-expenditure-government-expenditure, 2000 to 2021, UKR.svg" in titles
    assert "health-expenditure-government-expenditure, 2000 to 2022, YEM.svg" in titles
    # Ensure we are not pulling the "file" from owidslider or syntaxhighlight
    assert not any("(cropped).svg" in t for t in titles)


def test_get_titles_multiple_blocks_and_duplicates(sample_multiple_owidslidersrcs):
    """All File:... entries across multiple blocks are collected. Duplicates remain as-is."""
    titles = get_titles(sample_multiple_owidslidersrcs, filter_duplicates=False)
    assert titles == [
        "Alpha, 2000 to 2001, AAA.svg",
        "Beta, 2001 to 2002, BBB.svg",
        "Beta, 2001 to 2002, BBB.svg",  # duplicate preserved
        "Gamma, 2002 to 2003, CCC.svg",
    ]


def test_get_titles_empty_when_no_entries(sample_without_titles):
    """Returns empty list when owidslidersrcs contains no File entries."""
    assert get_titles(sample_without_titles) == []


@pytest.mark.parametrize(
    "block,expected_count",
    [
        # Single line with trailing attributes
        (
            "{{owidslidersrcs|id=x|widths=1|heights=1|gallery-AllCountries=\n"
            "File:Foo, 2000, AAA.svg!country=AAA\n}}",
            1,
        ),
        # Lines with spaces and commas inside
        (
            "{{owidslidersrcs|id=x|widths=1|heights=1|gallery-AllCountries=\n"
            "File:Foo Bar, 2001 to 2003, BBB.svg!country=BBB\n"
            "File:Zed, 1999 to 2000, CCC.svg!country=CCC\n}}",
            2,
        ),
        # No .svg files present
        ("{{owidslidersrcs|id=x|gallery-AllCountries=\n" "Not a file line\n}}", 0),
    ],
)
def test_get_titles_regex_variants(block, expected_count):
    """Regex should capture up to .svg and ignore anything after '!' or newlines."""
    titles = get_titles(block)
    assert len(titles) == expected_count
    assert all(t.endswith(".svg") for t in titles)
