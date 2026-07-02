# test_wikitext_processing.py

"""
Pytest test suite for:
- get_files_list_data
- get_titles
- get_titles_from_wikilinks

"""

from __future__ import annotations

import pytest

from src.main_app.utils.wikitext.temps_bot import (
    get_files_list_data,
    get_titles,
    get_titles_from_wikilinks,
)


def get_files_list(text: str, filter_duplicates: bool = True) -> tuple:
    data = get_files_list_data(text, filter_duplicates=filter_duplicates)
    return data["main_title"], data["titles"]


# ── texts fixtures ───────────────────────────────────────────────────────────────────


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


@pytest.fixture
def sample_without_titles() -> str:
    """Wikitext lacking both SVGLanguages and Translate line."""
    return "No main title here.\n{{owidslidersrcs|id=x|widths=100|heights=100|gallery-AllCountries=}}\n"


@pytest.fixture
def sample_with_both_titles() -> str:
    """Wikitext with both SVGLanguages and Translate line. SVGLanguages should take precedence."""
    return (
        "{{SVGLanguages|some_main_title,World,2010.svg}}\n"
        "*'''Translate''': https://svgtranslate.toolforge.org/File:another-title,World,2005.svg\n"
    )


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
            "{{owidslidersrcs|id=x|widths=1|heights=1|gallery-AllCountries=\nFile:Foo, 2000, AAA.svg!country=AAA\n}}",
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
        ("{{owidslidersrcs|id=x|gallery-AllCountries=\nNot a file line\n}}", 0),
    ],
)
def test_get_titles_regex_variants(block, expected_count):
    """Regex should capture up to .svg and ignore anything after '!' or newlines."""
    titles = get_titles(block)
    assert len(titles) == expected_count
    assert all(t.endswith(".svg") for t in titles)


# ---------- Tests for get_files_list (integration) ----------


def test_get_files_list_prefers_svglanguages(sample_with_both_titles, sample_multiple_owidslidersrcs):
    """get_files_list should return (main_title, titles) preferring SVGLanguages."""
    main, titles = get_files_list(
        sample_with_both_titles + "\n" + sample_multiple_owidslidersrcs, filter_duplicates=False
    )
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


def test_get_titles_from_wikilinks(sample_from_prompt: str):
    """Ensures wikilink-based SVG titles are extracted separately from owidslidersrcs titles."""
    titles = get_titles(sample_from_prompt)

    titles_new = get_titles_from_wikilinks(sample_from_prompt)

    assert "Health-expenditure-government-expenditure,World,2022 (cropped).svg" not in titles
    assert "Health-expenditure-government-expenditure,World,2022 (cropped).svg" in titles_new


class TestGetTitlesFromWikilinks:
    """Tests for the get_titles_from_wikilinks function."""

    def test_extract_single_file_link(self) -> None:
        """Test extracting a single file link."""
        text = "[[File:test.svg|link=|thumb|Description]]"
        result = get_titles_from_wikilinks(text)
        assert result == ["test.svg"]

    def test_extract_multiple_file_links(self) -> None:
        """Test extracting multiple file links."""
        text = "[[File:file1.svg|thumb]][[File:file2.svg|link=]]"
        result = get_titles_from_wikilinks(text)
        assert sorted(result) == ["file1.svg", "file2.svg"]

    def test_extract_file_link_with_spaces(self) -> None:
        """Test extracting file link with spaces in name."""
        text = "[[File:Test File.svg|thumb|Description]]"
        result = get_titles_from_wikilinks(text)
        assert result == ["Test File.svg"]

    def test_non_file_links_ignored(self) -> None:
        """Test that non-file links are ignored."""
        text = "[[Page Title|link text]] and [[File:test.svg|thumb]]"
        result = get_titles_from_wikilinks(text)
        assert result == ["test.svg"]

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = get_titles_from_wikilinks("")
        assert result == []

    def test_no_file_links(self) -> None:
        """Test text without file links."""
        text = "Some text without any file links"
        result = get_titles_from_wikilinks(text)
        assert result == []

    def test_file_link_without_extension_ignored(self) -> None:
        """Test that links without .svg extension are ignored."""
        text = "[[File:test.png|thumb]] and [[File:test2.jpg|link=]]"
        result = get_titles_from_wikilinks(text)
        # Only .svg files should be extracted
        assert result == []

    def test_mixed_file_extensions(self) -> None:
        """Test with mixed file extensions - only .svg extracted."""
        text = "[[File:test.svg|thumb]][[File:test.png|link=]][[File:another.svg]]"
        result = get_titles_from_wikilinks(text)
        assert sorted(result) == ["another.svg", "test.svg"]


class TestGetTitles:
    """Tests for the get_titles function."""

    def test_extract_from_owidslidersrcs(self) -> None:
        """Test extracting titles from {{owidslidersrcs}} template."""
        text = """
        {{owidslidersrcs|id=gallery
        |gallery-World=
        File:test1.svg!year=2020
        File:test2.svg!year=2021
        }}
        """
        result = get_titles(text, filter_duplicates=False)
        assert sorted(result) == ["test1.svg", "test2.svg"]

    def test_filter_duplicates(self) -> None:
        """Test that duplicates are filtered when filter_duplicates=True."""
        text = """
        {{owidslidersrcs
        |File:test.svg!year=2020
        |File:test.svg!year=2021
        }}
        """
        result = get_titles(text, filter_duplicates=True)
        assert result == ["test.svg"]

    def test_no_duplicates_filtering(self) -> None:
        """Test that duplicates are preserved when filter_duplicates=False."""
        text = """
        {{owidslidersrcs
        |File:test.svg!year=2020
        |File:test.svg!year=2021
        }}
        """
        result = get_titles(text, filter_duplicates=False)
        assert result == ["test.svg", "test.svg"]

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = get_titles("")
        assert result == []

    def test_no_owidslidersrcs_template(self) -> None:
        """Test text without {{owidslidersrcs}} template."""
        text = "Some text without the template"
        result = get_titles(text)
        assert result == []

    def test_case_insensitive_template_name(self) -> None:
        """Test that template name matching is case-insensitive."""
        text = """
        {{OWIDSLIDERSRCS
        |File:test.svg!year=2020
        }}
        """
        result = get_titles(text)
        assert result == ["test.svg"]

    def test_multiple_owidslidersrcs_templates(self) -> None:
        """Test extracting from multiple {{owidslidersrcs}} templates."""
        text = """
        {{owidslidersrcs|File:file1.svg!year=2020}}
        {{owidslidersrcs|File:file2.svg!year=2021}}
        """
        result = get_titles(text, filter_duplicates=False)
        assert sorted(result) == ["file1.svg", "file2.svg"]


class TestGetFilesList:
    """Tests for the get_files_list function."""

    def test_extract_main_title_and_titles(self) -> None:
        """Test extracting both main title and titles."""
        text = """
        {{SVGLanguages|test-file,World,2020.svg}}
        {{owidslidersrcs|File:title1.svg!year=2020}}
        """
        main_title, titles = get_files_list(text)
        assert main_title == "test-file,World,2020.svg"
        assert "title1.svg" in titles

    def test_main_title_underscores_to_spaces(self) -> None:
        """Test that underscores in main title are converted to spaces."""
        text = "{{SVGLanguages|test_file_name.svg}}"
        main_title, titles = get_files_list(text)
        assert main_title == "test file name.svg"

    def test_filter_duplicates(self) -> None:
        """Test that duplicates are filtered when filter_duplicates=True."""
        text = """
        {{SVGLanguages|test.svg}}
        {{owidslidersrcs|File:test.svg!year=2020}}
        """
        main_title, titles = get_files_list(text, filter_duplicates=True)
        assert "test.svg" in titles
        assert titles.count("test.svg") == 1

    def test_empty_text(self) -> None:
        """Test with empty text."""
        main_title, titles = get_files_list("")
        assert main_title is None
        assert titles == []

    def test_no_main_title(self) -> None:
        """Test when no main title can be found."""
        text = "{{owidslidersrcs|File:test.svg!year=2020}}"
        main_title, titles = get_files_list(text)
        assert main_title is None
        assert "test.svg" in titles

    def test_combined_wikilinks_and_owidslidersrcs(self) -> None:
        """Test extracting from both wikilinks and owidslidersrcs."""
        text = """
        {{SVGLanguages|main.svg}}
        {{owidslidersrcs|File:file1.svg!year=2020}}
        [[File:file2.svg|thumb|Description]]
        """
        main_title, titles = get_files_list(text)
        assert main_title == "main.svg"
        assert "file1.svg" in titles
        assert "file2.svg" in titles
