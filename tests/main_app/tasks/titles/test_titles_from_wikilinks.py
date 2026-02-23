# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- get_titles
- get_titles_from_wikilinks

Assumes the functions are available from the target module.
Replace `from your_module import ...` with your actual module name.
"""

import pytest

from src.main_app.tasks.titles.temps_bot import get_titles

# ---------- Fixtures with realistic wikitext samples ----------


@pytest.fixture
def sample_from_prompt() -> str:
    """Sample wikitext similar to the user's prompt."""
    return (
        "*[[Commons:List of interactive graphs|Return to list]]\n"
        "{{owidslider\n"
        "|start        = 2022\n"
        "|list         = Template:OWID/health expenditure government expenditure#gallery\n"
        "|location     = commons\n"
        "|caption      = \n"
        "|title        = \n"
        "|language     = \n"
        "|file         = [[File:Health-expenditure-government-expenditure,World,2022 (cropped).svg|link=|thumb|upright=1.6|Health expenditure government expenditure]]\n"
        "|startingView = World\n"
        "}}\n"
        '<syntaxhighlight lang="wikitext" style="overflow:auto;">\n'
        "{{owidslider\n"
        "|start        = 2022\n"
        "|list         = Template:OWID/health expenditure government expenditure#gallery\n"
        "|location     = commons\n"
        "|caption      = \n"
        "|title        = \n"
        "|language     = \n"
        "|file         = [[File:Health-expenditure-government-expenditure,World,2022 (cropped).svg|link=|thumb|upright=1.6|Health expenditure government expenditure]]\n"
        "|startingView = World\n"
        "}}\n"
        "</syntaxhighlight>\n"
        "*'''Source''': https://ourworldindata.org/grapher/health-expenditure-government-expenditure\n"
        "*'''Translate''':  https://svgtranslate.toolforge.org/File:health-expenditure-government-expenditure,World,2000.svg\n"
        "\n"
        "==Data==\n"
        "{{owidslidersrcs|id=gallery|widths=240|heights=240\n"
        "|gallery-AllCountries=\n"
        "File:health-expenditure-government-expenditure, 2000 to 2021, UKR.svg!country=UKR\n"
        "File:health-expenditure-government-expenditure, 2002 to 2022, AFG.svg!country=AFG\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, BGD.svg!country=BGD\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, FSM.svg!country=FSM\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, ERI.svg!country=ERI\n"
        "File:health-expenditure-government-expenditure, 2017 to 2022, SSD.svg!country=SSD\n"
        "File:health-expenditure-government-expenditure, 2013 to 2022, SOM.svg!country=SOM\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, YEM.svg!country=YEM\n"
        "}}\n"
    )


@pytest.fixture
def sample_without_titles() -> str:
    """Wikitext lacking both SVGLanguages and Translate line."""
    return "No main title here.\n{{owidslidersrcs|id=x|widths=100|heights=100|gallery-AllCountries=}}\n"


@pytest.fixture
def sample_multiple_owidslidersrcs() -> str:
    """Wikitext containing multiple owidslidersrcs blocks and duplicate filenames."""
    return (
        "{{owidslidersrcs|id=a|widths=120|heights=120|gallery-AllCountries=\n"
        "File:Alpha, 2000 to 2001, AAA.svg!country=AAA\n"
        "File:Beta, 2001 to 2002, BBB.svg!country=BBB\n"
        "}}\n"
        "{{owidslidersrcs|id=b|widths=120|heights=120|gallery-AllCountries=\n"
        "File:Beta, 2001 to 2002, BBB.svg!country=BBB\n"  # duplicate on purpose
        "File:Gamma, 2002 to 2003, CCC.svg!country=CCC\n"
        "}}\n"
    )


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
