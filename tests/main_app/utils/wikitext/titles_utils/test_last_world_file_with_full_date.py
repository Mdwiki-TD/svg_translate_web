"""
Tests for src/main_app/utils/wikitext/titles_utils/last_world_file_utils.py
Specifically for match_last_world_file_with_full_date function.
"""

from src.main_app.utils.wikitext.titles_utils.last_world_file_utils import (
    match_last_world_file_with_full_date,
)


class TestMatchLastWorldFileWithFullDate:
    """Tests for match_last_world_file_with_full_date function."""

    def test_empty_text_returns_empty(self):
        """Test that empty text returns empty string."""
        result = match_last_world_file_with_full_date("")
        assert result == ""

    def test_no_valid_lines_returns_empty(self):
        """Test that text without valid lines returns empty string."""
        result = match_last_world_file_with_full_date("Some random text\nMore text")
        assert result == ""

    def test_single_valid_line_with_full_date(self):
        """Test with single valid line containing full date."""
        text = "File:test, World, Apr 15, 1950.svg!year=Apr 15, 1950"
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test, World, Apr 15, 1950.svg"

    def test_multiple_lines_returns_latest_date(self):
        """Test that function returns file with latest full date."""
        text = """
File:youth mortality rate, World, Apr 15, 1950.svg!year=Apr 15, 1950
File:youth mortality rate, World, May 20, 1951.svg!year=May 20, 1951
File:youth mortality rate, World, Mar 10, 1951.svg!year=Mar 10, 1951
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:youth mortality rate, World, May 20, 1951.svg"

    def test_invalid_month_skipped(self):
        """Test that lines with invalid month are skipped."""
        text = """
File:test, World, Xyz 15, 1950.svg!year=Xyz 15, 1950
File:valid, World, Apr 15, 1950.svg!year=Apr 15, 1950
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:valid, World, Apr 15, 1950.svg"

    def test_invalid_year_format_skipped(self):
        """Test that lines with invalid year format are skipped."""
        text = """
File:test, World, 1950.svg!invalid_year
File:valid, World, Apr 15, 2000.svg!year=Apr 15, 2000
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:valid, World, Apr 15, 2000.svg"

    def test_line_without_exclamation_skipped(self):
        """Test that lines without ! are skipped."""
        text = """
File:test.svg
File:valid, World, Apr 15, 2000.svg!year=Apr 15, 2000
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:valid, World, Apr 15, 2000.svg"

    def test_underscores_replaced_with_spaces(self):
        """Test that underscores in filename are replaced with spaces."""
        text = "File:test_file_name, World, Apr 15, 1950.svg!year=Apr 15, 1950"
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test file name, World, Apr 15, 1950.svg"

    def test_filename_with_parentheses(self):
        """Test filename with parentheses."""
        text = "File:test_(example), World, Apr 15, 2020.svg!year=Apr 15, 2020"
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test (example), World, Apr 15, 2020.svg"

    def test_filename_with_hyphen(self):
        """Test filename with hyphen."""
        text = "File:test-file, World, Apr 15, 2020.svg!year=Apr 15, 2020"
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test-file, World, Apr 15, 2020.svg"

    def test_fallback_to_year_only(self):
        """Test fallback to year-only format when no full date."""
        text = """
File:test, World, 1950.svg!year=1950
File:test, World, 1960.svg!year=1960
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test, World, 1960.svg"

    def test_mixed_date_formats(self):
        """Test handling of mixed date formats (full date and year only)."""
        text = """
File:test, World, 1950.svg!year=1950
File:test, World, Apr 15, 1949.svg!year=Apr 15, 1949
File:test, World, 1955.svg!year=1955
        """
        result = match_last_world_file_with_full_date(text)
        # 1955 is the latest year
        assert result == "File:test, World, 1955.svg"

    def test_same_year_different_month(self):
        """Test comparing different months in the same year."""
        text = """
File:test, World, Dec 31, 2000.svg!year=Dec 31, 2000
File:test, World, Jan 1, 2000.svg!year=Jan 1, 2000
File:test, World, Jun 15, 2000.svg!year=Jun 15, 2000
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test, World, Dec 31, 2000.svg"

    def test_all_months(self):
        """Test all month abbreviations are recognized."""
        text = """
File:test, World, Jan 1, 2000.svg!year=Jan 1, 2000
File:test, World, Feb 2, 2000.svg!year=Feb 2, 2000
File:test, World, Mar 3, 2000.svg!year=Mar 3, 2000
File:test, World, Apr 4, 2000.svg!year=Apr 4, 2000
File:test, World, May 5, 2000.svg!year=May 5, 2000
File:test, World, Jun 6, 2000.svg!year=Jun 6, 2000
File:test, World, Jul 7, 2000.svg!year=Jul 7, 2000
File:test, World, Aug 8, 2000.svg!year=Aug 8, 2000
File:test, World, Sep 9, 2000.svg!year=Sep 9, 2000
File:test, World, Oct 10, 2000.svg!year=Oct 10, 2000
File:test, World, Nov 11, 2000.svg!year=Nov 11, 2000
File:test, World, Dec 12, 2000.svg!year=Dec 12, 2000
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test, World, Dec 12, 2000.svg"

    def test_whitespace_in_year_part(self):
        """Test handling of whitespace in year part."""
        text = "File:test, World, Apr 15, 1950.svg!  year  =  Apr 15, 1950  "
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test, World, Apr 15, 1950.svg"


class TestMatchLastWorldFileWithFullDateEdgeCases:
    """Edge case tests for match_last_world_file_with_full_date."""

    def test_invalid_filename_formats_skipped(self):
        """Test that various invalid filename formats are skipped."""
        text = """
NoFilePrefix.svg!year=Apr 15, 1950
File:.svg!year=Apr 15, 1950
File:test.txt!year=Apr 15, 1950
File:valid, World, Apr 15, 2000.svg!year=Apr 15, 2000
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:valid, World, Apr 15, 2000.svg"

    def test_single_digit_day(self):
        """Test handling of single digit day."""
        text = "File:test, World, Apr 5, 1950.svg!year=Apr 5, 1950"
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test, World, Apr 5, 1950.svg"

    def test_case_insensitive_month(self):
        """Test that month matching is case insensitive."""
        text = """
File:test, World, apr 15, 1950.svg!year=apr 15, 1950
File:test, World, APR 20, 1950.svg!year=APR 20, 1950
File:test, World, Apr 25, 1950.svg!year=Apr 25, 1950
        """
        result = match_last_world_file_with_full_date(text)
        assert result == "File:test, World, Apr 25, 1950.svg"
