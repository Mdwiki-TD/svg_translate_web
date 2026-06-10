"""Unit tests for src/main_app/core/jinja_filters.py module."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.main_app.core.jinja_filters import (
    filters,
    format_long_date,
    format_short_date,
    get_status_class,
    short_url,
)


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


class TestFormatLongDate:
    def test_iso_format_string(self):
        assert format_long_date("2026-05-28T23:51:50") == "2026-05-28 23:51:50"

    def test_datetime_object(self):
        dt = datetime(2025, 10, 27, 4, 41, 7)
        assert format_long_date(dt) == "2025-10-27 04:41:07"

    def test_empty_string_returns_default(self):
        assert format_long_date("") == ""

    def test_none_returns_default(self):
        assert format_long_date(None) == ""

    def test_custom_default(self):
        assert format_long_date("", default="N/A") == "N/A"

    def test_invalid_string_returns_default(self):
        assert format_long_date("not-a-date", default="bad") == "bad"


class TestFormatShortDate:
    def test_iso_format_string(self):
        assert format_short_date("2026-05-28T23:51:50") == "23:51:50"

    def test_datetime_object(self):
        dt = datetime(2025, 10, 27, 4, 41, 7)
        assert format_short_date(dt) == "04:41:07"

    def test_empty_string_returns_default(self):
        assert format_short_date("") == ""

    def test_none_returns_default(self):
        assert format_short_date(None) == ""


class TestGetStatusClass:
    @pytest.mark.parametrize(
        "status,expected",
        [
            ("running", "primary"),
            ("imported", "success"),
            ("imported_fallback", "success"),
            ("completed", "success"),
            ("changed", "success"),
            ("missing", "warning"),
            ("skipped", "warning"),
            ("cancelled", "warning"),
            ("failed", "danger"),
            ("error", "danger"),
            ("errors", "danger"),
            ("pending", "secondary"),
        ],
    )
    def test_known_statuses(self, status, expected):
        assert get_status_class(status) == expected

    def test_case_insensitive(self):
        assert get_status_class("RUNNING") == "primary"
        assert get_status_class("Failed") == "danger"

    def test_unknown_status_returns_secondary(self):
        assert get_status_class("unknown_status") == "secondary"

    def test_empty_string_returns_secondary(self):
        assert get_status_class("") == "secondary"


class TestFiltersDict:
    def test_filters_dict_has_all_keys(self):
        assert "format_long_date" in filters
        assert "format_short_date" in filters
        assert "get_status_class" in filters

    def test_filters_dict_values_are_callable(self):
        for key, func in filters.items():
            assert callable(func), f"filters[{key!r}] is not callable"
