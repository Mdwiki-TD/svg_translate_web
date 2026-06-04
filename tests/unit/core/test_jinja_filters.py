"""Tests for src/main_app/jinja_filters.py - Flask application factory."""

import pytest

from src.main_app.core.jinja_filters import short_url


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
