"""
Tests for src/main_app/utils/wikitext/template_page.py
"""

from __future__ import annotations

from src.main_app.utils.wikitext.template_page import update_template_page_file_reference


class TestUpdateTemplatePageFileReference:
    """Tests for the update_template_page_file_reference function."""

    def test_replace_file_reference_basic(self) -> None:
        """Test replacing a file reference in template page."""
        text = "[[File:Original.svg|link=|thumb|Description]]"
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == "[[File:Cropped.svg|link=|thumb|Description]]"

    def test_replace_file_reference_with_file_prefix(self) -> None:
        """Test replacing file reference when names include 'File:' prefix."""
        text = "[[File:Original.svg|link=|thumb]]"
        result = update_template_page_file_reference("File:Original.svg", "File:Cropped.svg", text)
        assert result == "[[File:Cropped.svg|link=|thumb]]"

    def test_replace_multiple_file_references(self) -> None:
        """Test replacing multiple file references."""
        text = "[[File:Original.svg|thumb]][[File:Original.svg|link=]]"
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == "[[File:Cropped.svg|thumb]][[File:Cropped.svg|link=]]"

    def test_replace_in_syntaxhighlight_block(self) -> None:
        """Test replacing file reference inside syntaxhighlight block."""
        text = '<syntaxhighlight lang="wikitext">[[File:Original.svg|thumb]]</syntaxhighlight>'
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert "[[File:Cropped.svg|thumb]]" in result

    def test_no_file_reference(self) -> None:
        """Test text without file reference returns unchanged."""
        text = "Some text without file references"
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == text

    def test_empty_text(self) -> None:
        """Test empty text returns empty."""
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", "")
        assert result == ""

    def test_partial_match_not_replaced(self) -> None:
        """Test that partial matches are not replaced."""
        text = "[[File:OriginalOld.svg|thumb]]"
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == text  # Should not change

    def test_different_file_not_replaced(self) -> None:
        """Test that different file references are not replaced."""
        text = "[[File:OtherFile.svg|thumb]]"
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == text

    def test_mixed_case_file_names(self) -> None:
        """Test that replacement is case-sensitive."""
        text = "[[File:original.svg|thumb]]"
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        # Case-sensitive, so no replacement
        assert result == text

    def test_file_reference_with_multiple_parameters(self) -> None:
        """Test replacing file reference with multiple parameters."""
        text = "[[File:Original.svg|link=|thumb|upright=1.6|Description text]]"
        result = update_template_page_file_reference("Original.svg", "Cropped.svg", text)
        assert result == "[[File:Cropped.svg|link=|thumb|upright=1.6|Description text]]"
