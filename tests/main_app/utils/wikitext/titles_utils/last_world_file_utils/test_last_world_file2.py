"""
Tests for src/main_app/utils/wikitext/titles_utils/last_world_file_utils.py
"""

from __future__ import annotations

from src.main_app.utils.wikitext.titles_utils.last_world_file_utils import (
    find_last_world_file_from_owidslidersrcs,
    match_last_world_file,
)


class TestMatchLastWorldFile:
    """Tests for the match_last_world_file function."""

    def test_find_last_file_by_year(self) -> None:
        """Test finding the file with the latest year."""
        text = """
        File:youth mortality rate, World, 1950.svg!year=1950
        File:youth mortality rate, World, 1951.svg!year=1951
        File:youth mortality rate, World, 1952.svg!year=1952
        File:youth mortality rate, World, 1953.svg!year=1953
        """
        result = match_last_world_file(text)
        assert result == "File:youth mortality rate, World, 1953.svg"

    def test_single_file(self) -> None:
        """Test with a single file entry."""
        text = "File:test.svg!year=2020"
        result = match_last_world_file(text)
        assert result == "File:test.svg"

    def test_unordered_years(self) -> None:
        """Test finding last file when years are not in order."""
        text = """
        File:test, World, 1953.svg!year=1953
        File:test, World, 1950.svg!year=1950
        File:test, World, 1952.svg!year=1952
        File:test, World, 1951.svg!year=1951
        """
        result = match_last_world_file(text)
        assert result == "File:test, World, 1953.svg"

    def test_underscores_replaced_with_spaces(self) -> None:
        """Test that underscores in filename are replaced with spaces."""
        text = "File:test_file_name, World, 2020.svg!year=2020"
        result = match_last_world_file(text)
        assert result == "File:test file name, World, 2020.svg"

    def test_invalid_line_format_ignored(self) -> None:
        """Test that lines without proper format are ignored."""
        text = """
        Invalid line without year
        File:test.svg!year=2020
        Another invalid line
        """
        result = match_last_world_file(text)
        assert result == "File:test.svg"

    def test_invalid_year_format_ignored(self) -> None:
        """Test that lines with invalid year format are ignored."""
        text = """
        File:test.svg!year=invalid
        File:test2.svg!year=2020
        """
        result = match_last_world_file(text)
        assert result == "File:test2.svg"

    def test_invalid_filename_format_ignored(self) -> None:
        """Test that lines with invalid filename format are ignored."""
        text = """
        NotAFile!year=2020
        File:test.svg!year=2020
        """
        result = match_last_world_file(text)
        assert result == "File:test.svg"

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = match_last_world_file("")
        assert result == ""

    def test_no_valid_files(self) -> None:
        """Test when no valid file entries exist."""
        text = """
        Invalid line 1
        Invalid line 2
        """
        result = match_last_world_file(text)
        assert result == ""

    def test_whitespace_stripped(self) -> None:
        """Test that whitespace is stripped from filenames."""
        text = "  File:test.svg!year=2020  "
        result = match_last_world_file(text)
        assert result == "File:test.svg"

    def test_complex_filename(self) -> None:
        """Test with complex filename containing special characters."""
        text = "File:health-expenditure(test), World, 2020.svg!year=2020"
        result = match_last_world_file(text)
        assert result == "File:health-expenditure(test), World, 2020.svg"


class TestFindLastWorldFileFromOwidslidersrcs:
    """Tests for the find_last_world_file_from_owidslidersrcs function."""

    def test_extract_from_gallery_world(self) -> None:
        """Test extracting last file from gallery-World argument."""
        text = """
        ==Data==
        {{owidslidersrcs|id=gallery|widths=240|heights=240
        |gallery-World=
        File:youth mortality rate, World, 1950.svg!year=1950
        File:youth mortality rate, World, 1951.svg!year=1951
        File:youth mortality rate, World, 1952.svg!year=1952
        File:youth mortality rate, World, 1953.svg!year=1953
        }}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result == "File:youth mortality rate, World, 1953.svg"

    def test_no_owidslidersrcs_template(self) -> None:
        """Test when no {{owidslidersrcs}} template exists."""
        text = "Some text without the template"
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result is None

    def test_no_gallery_world_argument(self) -> None:
        """Test when gallery-World argument is missing."""
        text = """
        {{owidslidersrcs|id=gallery
        |gallery-AllCountries=
        File:test.svg!country=XX
        }}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result is None

    def test_empty_gallery_world(self) -> None:
        """Test when gallery-World is empty."""
        text = """
        {{owidslidersrcs|gallery-World=
        }}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result is None

    def test_case_insensitive_template_name(self) -> None:
        """Test that template name matching is case-insensitive."""
        text = """
        {{OWIDSLIDERSRCS|gallery-World=
        File:test, World, 2020.svg!year=2020
        }}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result == "File:test, World, 2020.svg"

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = find_last_world_file_from_owidslidersrcs("")
        assert result is None

    def test_single_file_in_gallery(self) -> None:
        """Test with a single file in gallery-World."""
        text = """
        {{owidslidersrcs|gallery-World=
        File:single.svg!year=2020
        }}
        """
        result = find_last_world_file_from_owidslidersrcs(text)
        assert result == "File:single.svg"
