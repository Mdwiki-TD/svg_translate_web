# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- get_titles
- get_titles_from_wikilinks

"""
from __future__ import annotations

from src.main_app.utils.wikitext.temps_bot import (
    get_files_list,
    get_titles,
    get_titles_from_wikilinks,
)


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
