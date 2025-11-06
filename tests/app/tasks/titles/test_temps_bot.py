# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- get_files_list
"""

import pytest

from src.app.tasks.titles.temps_bot import get_files_list


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
        "<syntaxhighlight lang=\"wikitext\" style=\"overflow:auto;\">\n"
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
def sample_with_both_titles() -> str:
    """Wikitext with both SVGLanguages and Translate line. SVGLanguages should take precedence."""
    return (
        "{{SVGLanguages|some_main_title,World,2010.svg}}\n"
        "*'''Translate''': https://svgtranslate.toolforge.org/File:another-title,World,2005.svg\n"
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

# ---------- Tests for get_files_list (integration) ----------


def test_get_files_list_prefers_svglanguages(sample_with_both_titles, sample_multiple_owidslidersrcs):
    """get_files_list should return (main_title, titles) preferring SVGLanguages."""
    main, titles = get_files_list(sample_with_both_titles + "\n" + sample_multiple_owidslidersrcs, filter_duplicates=False)
    assert main == "some_main_title,World,2010.svg".replace("_", " ")
    assert len(titles) == 4
    assert "Gamma, 2002 to 2003, CCC.svg" in titles


def test_get_files_list_falls_back_to_translate(sample_from_prompt):
    """If no SVGLanguages then fallback to Translate regex."""
    main, titles = get_files_list(sample_from_prompt)
    assert main == "File:health-expenditure-government-expenditure,World,2000.svg"
    assert "health-expenditure-government-expenditure, 2000 to 2022, YEM.svg" in titles
    assert len(titles) == 9


def test_get_files_list_no_titles_no_main(sample_without_titles):
    """When neither titles nor main title exist."""
    main, titles = get_files_list(sample_without_titles)
    assert main is None
    assert titles == []
