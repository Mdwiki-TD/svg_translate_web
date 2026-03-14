# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- find_main_title

"""

import pytest

from src.main_app.utils.wikitext.titles_utils.main_file import find_main_title

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


def test_find_main_title_new():
    text = """*[[Commons:List of interactive graphs|Return to list]]
<syntaxhighlight lang="wikitext" style="overflow:auto;">
{{owidslider
|start        = 2024
|list         = Template:OWID/military spending as a share of GDP. SIPRI#gallery
|location     = commons
|caption      =
|title        =
|language     =
|file         = [[File:military-spending-as-a-share-of-gdp-sipri,World,2024 (cropped).svg|link=|thumb|upright=1.6|Military spending as a share of gdp sipri]]
|startingView = World
}}
</syntaxhighlight>
*'''Source''': https://ourworldindata.org/grapher/military-spending-as-a-share-of-gdp-sipri
*'''Translation''': https://svgtranslate.toolforge.org/File:Military-spending-as-a-share-of-gdp-sipri,World,1949.svg
{{-}}"""
    assert find_main_title(text) == "File:Military-spending-as-a-share-of-gdp-sipri,World,1949.svg"


class TestFindMainTitle:
    """Tests for the find_main_title function."""

    def test_priority_svglanguages_template(self) -> None:
        """Test that SVGLanguages template has highest priority."""
        text = """
        {{SVGLanguages|from-template.svg}}
        *'''Translate''': https://svgtranslate.toolforge.org/File:from-url.svg
        {{owidslidersrcs|gallery-World=File:from-owid.svg!year=2020}}
        """
        result = find_main_title(text)
        assert result == "from-template.svg"

    def test_fallback_to_url(self) -> None:
        """Test fallback to URL when no SVGLanguages template."""
        text = """
        *'''Translate''': https://svgtranslate.toolforge.org/File:from-url.svg
        {{owidslidersrcs|gallery-World=File:from-owid.svg!year=2020}}
        """
        result = find_main_title(text)
        assert result == "from-url.svg"

    def test_fallback_to_owidslidersrcs(self) -> None:
        """Test fallback to owidslidersrcs when no template or URL."""
        text = """
        {{owidslidersrcs|gallery-World=File:from-owid.svg!year=2020}}
        """
        result = find_main_title(text)
        assert result == "from-owid.svg"

    def test_no_main_title_found(self) -> None:
        """Test when no main title can be found."""
        text = "Some text without any title sources"
        result = find_main_title(text)
        assert result is None

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = find_main_title("")
        assert result is None

    def test_underscores_converted_to_spaces(self) -> None:
        """Test that underscores are converted to spaces in result."""
        text = "{{SVGLanguages|test_file_name.svg}}"
        result = find_main_title(text)
        assert result == "test file name.svg"

    def test_whitespace_stripped(self) -> None:
        """Test that whitespace is stripped from result."""
        text = "{{SVGLanguages|  test.svg  }}"
        result = find_main_title(text)
        assert result == "test.svg"
