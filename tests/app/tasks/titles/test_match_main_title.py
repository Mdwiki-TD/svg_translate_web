# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- match_main_title_from_url

Assumes the functions are available from the target module.
Replace `from your_module import ...` with your actual module name.
"""

import pytest

from src.app.tasks.titles.utils.main_file import match_main_title_from_url, match_main_title_from_url_new

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
def sample_with_svglanguages_only() -> str:
    """Wikitext with only SVGLanguages main title."""
    return "{{SVGLanguages|parkinsons-disease-prevalence-ihme,World,1990.svg}}\n" "Some other text...\n"


@pytest.fixture
def sample_with_both_titles() -> str:
    """Wikitext with both SVGLanguages and Translate line. SVGLanguages should take precedence."""
    return (
        "{{SVGLanguages|some_main_title,World,2010.svg}}\n"
        "*'''Translate''': https://svgtranslate.toolforge.org/File:another-title,World,2005.svg\n"
    )


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
