"""
Tests for src/main_app/utils/wikitext/files_text.py
"""

from __future__ import annotations

import pytest

from src.main_app.utils.wikitext.files_text import (
    appendImageExtractedTemplate,
    create_cropped_file_text,
    update_original_file_text,
)


class TestAppendImageExtractedTemplate:
    """Tests for the appendImageExtractedTemplate function."""

    def test_append_to_existing_template(self) -> None:
        """Test appending a file to an existing {{Image extracted}} template."""
        text = "{{Image extracted|1=File1.svg|2=File2.svg}}"
        result = appendImageExtractedTemplate("File3.svg", text)
        assert "|3=File3.svg}}" in result

    def test_file_already_exists_in_text(self) -> None:
        """Test that function returns original text if file already exists."""
        text = "{{Image extracted|1=File1.svg|2=File2.svg}}"
        result = appendImageExtractedTemplate("File2.svg", text)
        assert result == text

    def test_file_already_exists_case_insensitive(self) -> None:
        """Test that file existence check is case-insensitive."""
        text = "{{Image extracted|1=file1.svg}}"
        result = appendImageExtractedTemplate("FILE1.SVG", text)
        assert result == text

    def test_file_already_exists_with_underscores(self) -> None:
        """Test that file existence check handles underscores."""
        text = "{{Image extracted|1=File_One.svg}}"
        result = appendImageExtractedTemplate("File One.svg", text)
        assert result == text

    def test_no_template_returns_original(self) -> None:
        """Test that function returns original text if no template found."""
        text = "Some text without any template"
        result = appendImageExtractedTemplate("File3.svg", text)
        assert result == text

    def test_template_variations_image_extracted(self) -> None:
        """Test with {{Image extracted}} template variation."""
        text = "{{Image extracted|1=File1.svg}}"
        result = appendImageExtractedTemplate("File2.svg", text)
        assert "|2=File2.svg}}" in result

    def test_template_variations_extracted_image(self) -> None:
        """Test with {{Extracted image}} template variation."""
        text = "{{Extracted image|1=File1.svg}}"
        result = appendImageExtractedTemplate("File2.svg", text)
        assert "|2=File2.svg}}" in result

    def test_template_variations_cropped_version(self) -> None:
        """Test with {{Cropped version}} template variation."""
        text = "{{Cropped version|1=File1.svg}}"
        result = appendImageExtractedTemplate("File2.svg", text)
        assert "|2=File2.svg}}" in result

    def test_template_with_spaces(self) -> None:
        """Test template with extra spaces."""
        text = "{{ Image extracted | 1=File1.svg }}"
        result = appendImageExtractedTemplate("File2.svg", text)
        assert "|2=File2.svg" in result

    def test_file_name_with_file_prefix(self) -> None:
        """Test file name with 'File:' prefix is handled correctly."""
        text = "{{Image extracted|1=File1.svg}}"
        result = appendImageExtractedTemplate("File:File2.svg", text)
        assert "|2=File2.svg}}" in result

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = appendImageExtractedTemplate("File1.svg", "")
        assert result == ""


class TestUpdateOriginalFileText:
    """Tests for the update_original_file_text function."""

    def test_file_already_in_text(self) -> None:
        """Test that function returns original text if file already exists."""
        text = "Some text with File:Test.svg already present"
        result = update_original_file_text("File:Test.svg", text)
        assert result == text

    def test_file_already_in_text_case_insensitive(self) -> None:
        """Test that file existence check is case-insensitive."""
        text = "Some text with File:test.svg already present"
        result = update_original_file_text("File:TEST.SVG", text)
        assert result == text

    def test_adds_image_extracted_template(self) -> None:
        """Test that function adds {{Image extracted}} template."""
        text = "{{Information|description=Test}}"
        result = update_original_file_text("File:Cropped.svg", text)
        assert "{{Image extracted|1=Cropped.svg}}" in result

    def test_file_prefix_removed(self) -> None:
        """Test that 'File:' prefix is removed from cropped file name."""
        text = "{{Information}}"
        result = update_original_file_text("File:Test.svg", text)
        assert "Test.svg" in result
        assert "File:Test.svg" not in result.split("|1=")[1] if "|1=" in result else True

    def test_underscores_replaced_with_spaces(self) -> None:
        """Test that underscores in file name are replaced with spaces."""
        text = "{{Information}}"
        result = update_original_file_text("File:Test_File.svg", text)
        assert "Test File.svg" in result

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = update_original_file_text("File:Test.svg", "")
        # Empty text with no templates returns empty string
        assert result == ""


class TestCreateCroppedFileText:
    """Tests for the create_cropped_file_text function."""

    def test_add_extracted_from_template(self) -> None:
        """Test that function adds {{Extracted from}} template."""
        text = "{{Information|description=Test}}"
        result = create_cropped_file_text("File:Original.svg", text)
        assert "{{Extracted from|1=Original.svg}}" in result

    def test_empty_text(self) -> None:
        """Test with empty text returns just the template."""
        result = create_cropped_file_text("File:Original.svg", "")
        assert result == "{{Extracted from|1=Original.svg}}"

    def test_file_prefix_removed(self) -> None:
        """Test that 'File:' prefix is removed from file name."""
        text = "{{Information}}"
        result = create_cropped_file_text("File:Original.svg", text)
        assert "Original.svg" in result
        assert "File:Original.svg" not in result.split("|1=")[1] if "|1=" in result else True

    def test_template_added_to_existing_content(self) -> None:
        """Test that template is added to existing content."""
        text = "{{Information|description=A cropped image}}"
        result = create_cropped_file_text("File:Original.svg", text)
        # The other versions parameter is added to the Information template
        assert "|other versions=" in result
        assert "{{Extracted from|1=Original.svg}}" in result

    def test_fallback_to_insert_before_methods(self) -> None:
        """Test fallback to insert_before_methods when add_other_versions fails (line 90)."""
        # Text without {{Information}} template - should fallback to insert_before_methods
        text = "Just plain text without any templates"
        result = create_cropped_file_text("File:Original.svg", text)
        # The function should add the Extracted from template at the end
        assert "{{Extracted from|1=Original.svg}}" in result
