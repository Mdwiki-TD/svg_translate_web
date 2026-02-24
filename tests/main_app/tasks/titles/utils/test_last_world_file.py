"""Tests for tasks/titles/utils/last_world_file module."""

import pytest

from src.main_app.tasks.titles.utils.last_world_file import (
    find_last_world_file_from_owidslidersrcs,
    match_last_world_file,
)


class TestMatchLastWorldFile:
    """Tests for match_last_world_file function."""

    def test_empty_text_returns_empty(self):
        """Test that empty text returns empty string."""
        result = match_last_world_file("")
        assert result == ""

    def test_no_valid_lines_returns_empty(self):
        """Test that text without valid lines returns empty string."""
        result = match_last_world_file("Some random text\nMore text")
        assert result == ""

    def test_single_valid_line(self):
        """Test with single valid line."""
        text = "File:test, World, 1950.svg!year=1950"
        result = match_last_world_file(text)
        assert result == "File:test, World, 1950.svg"

    def test_multiple_lines_returns_latest_year(self):
        """Test that function returns file with latest year."""
        text = """
File:youth mortality rate, World, 1950.svg!year=1950
File:youth mortality rate, World, 1951.svg!year=1951
File:youth mortality rate, World, 1953.svg ! year = 1953
File:youth mortality rate, World, 1952.svg ! year=1952
        """
        result = match_last_world_file(text)
        assert result == "File:youth mortality rate, World, 1953.svg"

    def test_invalid_filename_skipped(self):
        """Test that lines with invalid filenames are skipped."""
        text = """
Invalid filename!year=1950
File:valid, World, 2000.svg!year=2000
        """
        result = match_last_world_file(text)
        assert result == "File:valid, World, 2000.svg"

    def test_invalid_year_format_skipped(self):
        """Test that lines with invalid year format are skipped."""
        text = """
File:test, World, 1950.svg!invalid_year
File:valid, World, 2000.svg!year=2000
        """
        result = match_last_world_file(text)
        assert result == "File:valid, World, 2000.svg"

    def test_line_without_exclamation_skipped(self):
        """Test that lines without ! are skipped."""
        text = """
File:test.svg
File:valid, World, 2000.svg!year=2000
        """
        result = match_last_world_file(text)
        assert result == "File:valid, World, 2000.svg"

    def test_underscores_replaced_with_spaces(self):
        """Test that underscores in filename are replaced with spaces."""
        text = "File:test_file_name, World, 1950.svg!year=1950"
        result = match_last_world_file(text)
        assert result == "File:test file name, World, 1950.svg"

    def test_filename_with_parentheses(self):
        """Test filename with parentheses."""
        text = "File:test_(example), World, 2020.svg!year=2020"
        result = match_last_world_file(text)
        assert result == "File:test (example), World, 2020.svg"

    def test_filename_with_hyphen(self):
        """Test filename with hyphen."""
        text = "File:test-file, World, 2020.svg!year=2020"
        result = match_last_world_file(text)
        assert result == "File:test-file, World, 2020.svg"

    def test_multiple_different_years(self):
        """Test with multiple different years."""
        text = """
File:chart, World, 1900.svg!year=1900
File:chart, World, 2023.svg!year=2023
File:chart, World, 1999.svg!year=1999
File:chart, World, 2050.svg!year=2050
        """
        result = match_last_world_file(text)
        assert result == "File:chart, World, 2050.svg"


class TestFindLastWorldFileFromOwidslidersrcs:
    """Tests for find_last_world_file_from_owidslidersrcs function."""

    def test_empty_text_returns_none(self):
        """Test that empty text returns None."""
        result = find_last_world_file_from_owidslidersrcs("")
        assert result is None

    def test_no_template_returns_none(self):
        """Test that text without template returns None."""
        text = "Some text without template"
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result is None

    def test_template_without_gallery_world_returns_none(self):
        """Test that template without gallery-World returns None."""
        text = """
{{owidslidersrcs|id=gallery|widths=240
|gallery-Asia=File:test.svg
}}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result is None

    def test_valid_template_returns_last_world_file(self):
        """Test valid template with gallery-World."""
        text = """
==Data==
{{owidslidersrcs|id=gallery|widths=240|heights=240
|gallery-World=
File:youth mortality rate, World, 1950.svg!year=1950
File:youth mortality rate, World, 1951.svg!year=1951
File:youth mortality rate, World, 1953.svg!year=1953
}}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result == "File:youth mortality rate, World, 1953.svg"

    def test_case_insensitive_template_name(self):
        """Test that template name is case insensitive."""
        text = """
{{Owidslidersrcs|id=gallery|widths=240
|gallery-World=File:test, World, 2000.svg!year=2000
}}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result == "File:test, World, 2000.svg"

    def test_template_with_whitespace_in_name(self):
        """Test template with whitespace in name."""
        text = """
{{ owidslidersrcs |id=gallery|widths=240
|gallery-World=File:test, World, 2000.svg!year=2000
}}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result == "File:test, World, 2000.svg"

    def test_multiple_templates_uses_first(self):
        """Test that first matching template is used."""
        text = """
{{owidslidersrcs|id=gallery|widths=240
|gallery-World=File:first, World, 2000.svg!year=2000
}}
{{owidslidersrcs|id=gallery2|widths=240
|gallery-World=File:second, World, 2020.svg!year=2020
}}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result == "File:first, World, 2000.svg"
