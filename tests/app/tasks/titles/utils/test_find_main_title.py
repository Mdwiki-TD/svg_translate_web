# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- find_main_title

"""

import pytest

from src.app.tasks.titles.utils.main_file import find_main_title


@pytest.fixture
def sample_with_svglanguages_only() -> str:
    """Wikitext with only SVGLanguages main title."""
    return (
        "{{SVGLanguages|parkinsons-disease-prevalence-ihme,World,1990.svg}}\n"
        "Some other text...\n"
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

# ---------- Tests for find_main_title ----------


def test_find_main_title_svglanguages(sample_with_svglanguages_only):
    """SVGLanguages should be parsed and returned as-is except underscores replaced with spaces."""
    got = find_main_title(sample_with_svglanguages_only)
    assert got == "parkinsons-disease-prevalence-ihme,World,1990.svg".replace("_", " ")


def test_find_main_title_prefers_svglanguages_over_translate(sample_with_both_titles):
    """SVGLanguages takes precedence when both exist."""
    got = find_main_title(sample_with_both_titles)
    assert got == "some_main_title,World,2010.svg".replace("_", " ")


def test_find_main_title_none_when_absent(sample_without_titles):
    """Return None if no SVGLanguages present."""
    assert find_main_title(sample_without_titles) is None


# ---------- Robustness and corner cases ----------

@pytest.mark.parametrize(
    "tpl,expected",
    [
        ("{{SVGLanguages|Title_With_Underscores,World,2020.svg}}", "Title With Underscores,World,2020.svg"),
        ("{{ SVGLanguages | spaced_title,World,2015.svg }}", "spaced title,World,2015.svg"),
        # Case-insensitive template name handling
        ("{{svglanguages|MiXeD-Case,World,2012.svg}}", "MiXeD-Case,World,2012.svg"),
    ],
)
def test_find_main_title_variants(tpl, expected):
    """Whitespace and case variations are handled."""
    assert find_main_title(tpl) == expected
