"""Tests for src/main_app/jinja_filters.py - Flask application factory."""

import pytest

from src.main_app.utils.jinja_filters import format_stage_timestamp, short_url


class TestFormatStageTimestamp:
    """Tests for format_stage_timestamp Jinja filter."""

    def test_format_stage_timestamp_valid(self):
        """Test format_stage_timestamp with valid ISO8601 timestamp."""
        result = format_stage_timestamp("2025-10-27T04:41:07")
        assert result == "Oct 27, 2025, 4:41 AM"

    def test_format_stage_timestamp_afternoon(self):
        """Test format_stage_timestamp with afternoon time."""
        result = format_stage_timestamp("2025-10-27T14:30:00")
        assert result == "Oct 27, 2025, 2:30 PM"

    def test_format_stage_timestamp_midnight(self):
        """Test format_stage_timestamp with midnight."""
        result = format_stage_timestamp("2025-10-27T00:00:00")
        assert result == "Oct 27, 2025, 12:00 AM"

    def test_format_stage_timestamp_noon(self):
        """Test format_stage_timestamp with noon."""
        result = format_stage_timestamp("2025-10-27T12:00:00")
        assert result == "Oct 27, 2025, 12:00 PM"

    def test_format_stage_timestamp_empty_string(self):
        """Test format_stage_timestamp with empty string."""
        result = format_stage_timestamp("")
        assert result == ""

    def test_format_stage_timestamp_none(self):
        """Test format_stage_timestamp with None-like value."""
        result = format_stage_timestamp(None)
        assert result == ""

    def test_format_stage_timestamp_invalid_format(self):
        """Test format_stage_timestamp with invalid timestamp format."""
        result = format_stage_timestamp("invalid-timestamp")
        assert result == ""

    def test_format_stage_timestamp_with_microseconds(self):
        """Test format_stage_timestamp with microseconds."""
        result = format_stage_timestamp("2025-10-27T04:41:07.123456")
        assert result == "Oct 27, 2025, 4:41 AM"

    def test_format_stage_timestamp_different_months(self):
        """Test format_stage_timestamp with different months."""
        assert "Jan" in format_stage_timestamp("2025-01-15T10:30:00")
        assert "Feb" in format_stage_timestamp("2025-02-15T10:30:00")
        assert "Dec" in format_stage_timestamp("2025-12-15T10:30:00")

    def test_format_stage_timestamp_edge_time_values(self):
        """Test format_stage_timestamp with edge case time values."""
        # Test 11 AM (should show as 11 AM, not 11 PM)
        result = format_stage_timestamp("2025-10-27T11:00:00")
        assert result == "Oct 27, 2025, 11:00 AM"

        # Test 1 AM
        result = format_stage_timestamp("2025-10-27T01:00:00")
        assert result == "Oct 27, 2025, 1:00 AM"

        # Test 11 PM
        result = format_stage_timestamp("2025-10-27T23:00:00")
        assert result == "Oct 27, 2025, 11:00 PM"

        # Test 1 PM
        result = format_stage_timestamp("2025-10-27T13:00:00")
        assert result == "Oct 27, 2025, 1:00 PM"


class TestShortUrl:
    """Tests for short_url function."""

    @pytest.mark.parametrize(
        "input_url, expected",
        [
            ("https://www.example.com/long/url", "url"),  # normal URL
            ("https://www.example.com/long/url/", "url"),  # trailing slash
            ("https://www.example.com/long/url?query=1", "url"),  # with query
            ("", ""),  # empty string
            (None, ""),  # None input
            ("/just/path/segment", "segment"),  # relative path
            ("segment_only", "segment_only"),  # no slashes
        ],
    )
    def test_short_url_various(self, input_url, expected):
        assert short_url(input_url) == expected

    def test_short_url_exception_handling(self):
        """Test short_url handles exceptions gracefully."""
        # Test with non-string input that might cause rsplit to fail
        result = short_url(12345)  # integer input
        assert result == ""
