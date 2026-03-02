"""Tests for the wikitext module."""

from __future__ import annotations

from src.main_app.jobs_workers.crop_main_files.wikitext import update_template_page_file_reference


class TestUpdateTemplatePageFileReference:
    """Tests for the update_template_page_file_reference function."""

    def test_replaces_file_reference_in_template(self):
        """Test replacing file reference in a template page."""
        text = """|file         = [[File:barley yields, World, 2023.svg|link=|thumb|upright=1.6|Barley yields]]"""
        result = update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert "[[File:barley yields, World, 2023 (cropped).svg|" in result
        assert "[[File:barley yields, World, 2023.svg|" not in result

    def test_replaces_all_occurrences_including_syntaxhighlight(self):
        """Test that all occurrences are replaced, including in syntaxhighlight blocks."""
        text = (
            "{{owidslider\n"
            "|file         = [[File:barley yields, World, 2023.svg|link=|thumb|upright=1.6|Barley yields]]\n"
            "}}\n"
            '<syntaxhighlight lang="wikitext">\n'
            "{{owidslider\n"
            "|file         = [[File:barley yields, World, 2023.svg|link=|thumb|upright=1.6|Barley yields]]\n"
            "}}\n"
            "</syntaxhighlight>"
        )
        result = update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert result.count("[[File:barley yields, World, 2023 (cropped).svg|") == 2
        assert "[[File:barley yields, World, 2023.svg|" not in result

    def test_handles_filename_without_file_prefix(self):
        """Test that filenames without File: prefix are handled correctly."""
        text = "|file = [[File:barley yields, World, 2023.svg|link=]]"
        result = update_template_page_file_reference(
            "barley yields, World, 2023.svg",
            "barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert "[[File:barley yields, World, 2023 (cropped).svg|" in result
        assert "[[File:barley yields, World, 2023.svg|" not in result

    def test_returns_unchanged_text_when_no_match(self):
        """Test that text is returned unchanged when original file is not found."""
        text = "|file = [[File:other file.svg|link=]]"
        result = update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            text,
        )
        assert result == text

    def test_returns_unchanged_empty_text(self):
        """Test that empty text is returned unchanged."""
        result = update_template_page_file_reference(
            "File:barley yields, World, 2023.svg",
            "File:barley yields, World, 2023 (cropped).svg",
            "",
        )
        assert result == ""
