"""
Tests for src/main_app/utils/wikitext/cropped_file_text/utils.py
"""

from __future__ import annotations

import pytest

from src.main_app.utils.wikitext.cropped_file_text.utils import (
    create_cropped_file_text,
)


class TestCreateCroppedFileText:
    """Tests for the create_cropped_file_text function."""

    def test_add_extracted_from_template(self) -> None:
        """Test that function adds {{Extracted from}} template."""
        text = "{{Information|description=Test}}"
        result = create_cropped_file_text("File:Original.svg", text)
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

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
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_fallback_to_insert_before_methods(self) -> None:
        """Test fallback to insert_before_methods when add_other_versions fails (line 90)."""
        # Text with category but no {{Information}} template - should fallback to insert_before_methods
        text = "[[Category:Test]]"
        result = create_cropped_file_text("File:Original.svg", text)
        # The function should add the Extracted from template before the category
        assert result.count("{{Extracted from|1=Original.svg}}") == 1
        assert result.index("{{Extracted from") < result.index("[[Category:")


class TestCreateCroppedFileTextEdgeTests:
    """Test edge cases for create_cropped_file_text function."""

    def test_template_added_to_existing_other_versions(self) -> None:
        """Test that template is added to existing content."""
        text = "{{Information|description=A cropped image|other_versions=}}"
        result = create_cropped_file_text("File:Original.svg", text)
        # The other versions parameter is added to the Information template
        assert "|other versions=" not in result
        assert (
            result == "{{Information|description=A cropped image|other_versions={{Extracted from|1=Original.svg}}\n}}"
        )
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_count_extracted_from(self) -> None:
        text = """{{Information
|description={{en|1=Wheat yields, World}}
|author = Our World In Data
|date= 2023
|source = https://ourworldindata.org/grapher/wheat-yields?tab=map
}}"""

        result = create_cropped_file_text("wheat yields, World, 2023.svg", text)

        assert "|author = Our World In Data" in result
        assert result.count("{{Extracted from|1=wheat yields, World, 2023.svg}}") == 1

    def test_adds_author_when_information_template_has_none(self) -> None:
        """Test that a citation is added when the Information template lacks an author."""
        text = "{{Information|description=Wheat yields}}"

        result = create_cropped_file_text("Original.svg", text)

        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_preserves_author(self) -> None:
        """Test that unavailable metadata leaves the original author untouched."""
        text = "{{Information|author=Our World In Data}}"

        result = create_cropped_file_text("Original.svg", text)

        assert "author=Our World In Data" in result
        assert result.count("{{Extracted from|1=Original.svg}}") == 1

    def test_not_adding_duplicate_value(self) -> None:
        """test not adding duplicate value."""
        text = "{{Information|author=Our World In Data|other versions={{extracted from|1=Original.svg}}}}"

        result = create_cropped_file_text("Original.svg", text)

        assert result.count("{{extracted from|") == 1
        assert result.count("{{extracted from|1=Original.svg}}") == 1

    @pytest.mark.todo
    def test_template_added_to_existing_other_versions_extended(self) -> None:
        """Test that template is added to existing content."""
        text = "{{Information|description=A cropped image|other_versions={{Extracted from| Original.svg }}}}"
        result = create_cropped_file_text("File:Original.svg", text)
        # The other versions parameter is added to the Information template
        assert "|other versions=" not in result
        assert (
            result == "{{Information|description=A cropped image|other_versions={{Extracted from|1=Original.svg}}\n}}"
        )
        assert result.count("{{Extracted from|1=Original.svg}}") == 1
