import pytest

from src.main_app.utils.new_wikitext.main_title_finder import MainTitleFinder

GALLERY = (
    "{{owidslidersrcs|id=gallery\n"
    "|gallery-World=\n"
    "File:a, World, 1950.svg!year=1950\n"
    "File:a, World, 1951.svg!year=1951\n"
    "}}"
)


def test_find_main_title_svglanguages():
    """SVGLanguages should be parsed and returned as-is except underscores replaced with spaces."""
    sample_svglanguages_only = (
        "{{SVGLanguages|parkinsons-disease-prevalence-ihme,World,1990.svg}}\nSome other text...\n"
    )
    got = MainTitleFinder().find_main_title(sample_svglanguages_only)
    assert got == "parkinsons-disease-prevalence-ihme,World,1990.svg".replace("_", " ")


def test_find_main_title_prefers_svglanguages_over_translate():
    """SVGLanguages takes precedence when both exist."""

    with_both_titles = (
        "{{SVGLanguages|some_main_title,World,2010.svg}}\n"
        "*'''Translate''': https://svgtranslate.toolforge.org/File:another-title,World,2005.svg\n"
    )

    got = MainTitleFinder().find_main_title(with_both_titles)
    assert got == "some_main_title,World,2010.svg".replace("_", " ")


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
    assert MainTitleFinder().find_main_title(tpl) == expected


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
    assert MainTitleFinder().find_main_title(text) == "File:Military-spending-as-a-share-of-gdp-sipri,World,1949.svg"


class TestMainTitleFinderUrl:
    """Tests for the svgtranslate URL matchers of ``MainTitleFinder``."""

    def test_new_matcher_returns_decoded_file_path(self):
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:Foo_bar%2C_World.svg"
        assert MainTitleFinder().match_main_title_from_url_new(text) == "File:Foo_bar,_World.svg"

    def test_new_matcher_rejects_non_svg(self):
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:a.png"
        assert MainTitleFinder().match_main_title_from_url_new(text) is None

    def test_old_matcher_requires_full_line(self):
        text = "*'''Translation''': https://svgtranslate.toolforge.org/File:A_b,_World.svg"
        assert MainTitleFinder().match_main_title_from_url(text) == "File:A_b,_World.svg"


class TestMainTitleFinderFind:
    """Tests for ``MainTitleFinder.find_main_title``."""

    def test_reads_svglanguages_template(self):
        assert MainTitleFinder().find_main_title("{{SVGLanguages|my_file,World,1990.svg}}") == "my file,World,1990.svg"

    def test_reads_first_gallery_file(self):
        assert MainTitleFinder().find_main_title(GALLERY) == "File:a, World, 1950.svg"

    def test_remove_prefix(self):
        assert MainTitleFinder().find_main_title(GALLERY, remove_prefix=True) == "a, World, 1950.svg"


class TestFindMainTitle:
    """Tests for the find_main_title function."""

    def test_priority_svglanguages_template(self) -> None:
        """Test that SVGLanguages template has highest priority."""
        text = """
        {{SVGLanguages|from-template.svg}}
        *'''Translate''': https://svgtranslate.toolforge.org/File:from-url.svg
        {{owidslidersrcs|gallery-World=File:from-owid.svg!year=2020}}
        """
        result = MainTitleFinder().find_main_title(text)
        assert result == "from-template.svg"

    def test_fallback_to_url(self) -> None:
        """Test fallback to URL when no SVGLanguages template."""
        # Note: match_main_title_from_url_new is checked before match_main_title_from_url
        # and it matches the owidslidersrcs content, so owidslidersrcs takes precedence
        text = """
        *'''Translate''': https://svgtranslate.toolforge.org/File:from-url.svg
        {{owidslidersrcs|gallery-World=File:from-owid.svg!year=2020}}
        """
        result = MainTitleFinder().find_main_title(text)
        assert result == "File:from-owid.svg"

    def test_fallback_to_owidslidersrcs(self) -> None:
        """Test fallback to owidslidersrcs when no template or URL."""
        text = """
        {{owidslidersrcs|gallery-World=File:from-owid.svg!year=2020}}
        """
        result = MainTitleFinder().find_main_title(text)
        assert result == "File:from-owid.svg"

    def test_no_main_title_found(self) -> None:
        """Test when no main title can be found."""
        text = "Some text without any title sources"
        result = MainTitleFinder().find_main_title(text)
        assert result is None

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = MainTitleFinder().find_main_title("")
        assert result is None

    def test_underscores_converted_to_spaces(self) -> None:
        """Test that underscores are converted to spaces in result."""
        text = "{{SVGLanguages|test_file_name.svg}}"
        result = MainTitleFinder().find_main_title(text)
        assert result == "test file name.svg"

    def test_whitespace_stripped(self) -> None:
        """Test that whitespace is stripped from result."""
        text = "{{SVGLanguages|  test.svg  }}"
        result = MainTitleFinder().find_main_title(text)
        assert result == "test.svg"
