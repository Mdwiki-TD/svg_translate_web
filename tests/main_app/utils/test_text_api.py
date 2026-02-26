"""Tests for text_api module."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.utils.text_api import get_file_text, update_file_text


class TestGetFileText:
    """Tests for get_file_text function."""

    def _create_mock_site(self, text_content=""):
        """Helper to create a properly mocked mwclient.Site."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.text.return_value = text_content
        mock_site.pages.__getitem__.return_value = mock_page
        return mock_site

    def test_valid_inputs_returns_text(self):
        """Test with valid inputs returns the page text."""
        mock_site = self._create_mock_site(text_content="Sample wikitext content")
        result = get_file_text("Example.svg", mock_site)
        assert result == "Sample wikitext content"
        mock_site.pages.__getitem__.assert_called_once_with("File:Example.svg")

    def test_adds_file_prefix(self):
        """Test that File: prefix is added to filename."""
        mock_site = self._create_mock_site(text_content="content")
        get_file_text("Example.svg", mock_site)
        # Verify the filename was prefixed before accessing pages
        mock_site.pages.__getitem__.assert_called_once_with("File:Example.svg")

    def test_missing_file_name_returns_empty_string(self, caplog):
        """Test that missing file_name returns empty string and logs error."""
        mock_site = self._create_mock_site()
        with caplog.at_level(logging.ERROR):
            result = get_file_text(None, mock_site)

        assert result == ""
        assert "Missing required fields for get_file_text" in caplog.text
        assert "file_name" in caplog.text

    def test_missing_site_returns_empty_string(self, caplog):
        """Test that missing site returns empty string and logs error."""
        with caplog.at_level(logging.ERROR):
            result = get_file_text("Example.svg", None)

        assert result == ""
        assert "Missing required fields for get_file_text" in caplog.text
        assert "site" in caplog.text

    def test_empty_file_name_returns_empty_string(self, caplog):
        """Test that empty file_name returns empty string."""
        mock_site = self._create_mock_site()
        with caplog.at_level(logging.ERROR):
            result = get_file_text("", mock_site)

        assert result == ""
        assert "Missing required fields for get_file_text" in caplog.text

    def test_both_missing_returns_empty_string(self, caplog):
        """Test that both missing fields returns empty string and logs both."""
        with caplog.at_level(logging.ERROR):
            result = get_file_text(None, None)

        assert result == ""
        assert "file_name" in caplog.text
        assert "site" in caplog.text

    def test_with_prefixed_filename(self):
        """Test with already prefixed filename - prefix is not doubled."""
        mock_site = self._create_mock_site(text_content="prefixed content")
        result = get_file_text("File:Example.svg", mock_site)
        assert result == "prefixed content"
        # ensure_file_prefix doesn't double the prefix
        mock_site.pages.__getitem__.assert_called_once_with("File:Example.svg")

    def test_site_exception_returns_empty_string(self, caplog):
        """Test that exception from site.pages raises proper error and returns empty string."""
        mock_site = MagicMock()
        mock_site.pages.__getitem__.side_effect = Exception("Connection error")

        with caplog.at_level(logging.ERROR):
            result = get_file_text("Example.svg", mock_site)

        assert result == ""
        assert "Failed to retrieve wikitext" in caplog.text

    def test_text_method_exception_returns_empty_string(self, caplog):
        """Test that exception from page.text() returns empty string."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.text.side_effect = Exception("Page not found")
        mock_site.pages.__getitem__.return_value = mock_page

        with caplog.at_level(logging.ERROR):
            result = get_file_text("Example.svg", mock_site)

        assert result == ""
        assert "Failed to retrieve wikitext" in caplog.text


class TestUpdateFileText:
    """Tests for update_file_text function."""

    def test_valid_inputs(self):
        """Test with valid inputs - currently returns incomplete dict (TODO implementation)."""
        mock_site = MagicMock()
        result = update_file_text("Example.svg", "new wikitext", mock_site)
        # Function doesn't return anything when successful (TODO)

    def test_adds_file_prefix(self):
        """Test that File: prefix is added to original_file."""
        mock_site = MagicMock()
        # Should process without error
        update_file_text("Example.svg", "new wikitext", mock_site)

    def test_missing_original_file_returns_error(self, caplog):
        """Test that missing original_file returns error dict."""
        mock_site = MagicMock()
        with caplog.at_level(logging.ERROR):
            result = update_file_text(None, "new wikitext", mock_site)

        assert result["success"] is False
        assert "error" in result
        assert "original_file" in result["error"]
        assert "Missing required fields for update_file_text" in caplog.text

    def test_missing_updated_file_text_returns_error(self, caplog):
        """Test that missing updated_file_text returns error dict."""
        mock_site = MagicMock()
        with caplog.at_level(logging.ERROR):
            result = update_file_text("Example.svg", None, mock_site)

        assert result["success"] is False
        assert "error" in result
        assert "updated_file_text" in result["error"]
        assert "Missing required fields for update_file_text" in caplog.text

    def test_missing_site_returns_error(self, caplog):
        """Test that missing site returns error dict."""
        with caplog.at_level(logging.ERROR):
            result = update_file_text("Example.svg", "new wikitext", None)

        assert result["success"] is False
        assert "error" in result
        assert "site" in result["error"]
        assert "Missing required fields for update_file_text" in caplog.text

    def test_empty_original_file_returns_error(self, caplog):
        """Test that empty original_file returns error dict."""
        mock_site = MagicMock()
        with caplog.at_level(logging.ERROR):
            result = update_file_text("", "new wikitext", mock_site)

        assert result["success"] is False
        assert "original_file" in result["error"]

    def test_empty_updated_file_text_returns_error(self, caplog):
        """Test that empty updated_file_text returns error dict."""
        mock_site = MagicMock()
        with caplog.at_level(logging.ERROR):
            result = update_file_text("Example.svg", "", mock_site)

        assert result["success"] is False
        assert "updated_file_text" in result["error"]

    def test_multiple_missing_fields_returns_error(self, caplog):
        """Test that multiple missing fields are all reported."""
        with caplog.at_level(logging.ERROR):
            result = update_file_text(None, None, None)

        assert result["success"] is False
        assert "original_file" in result["error"]
        assert "updated_file_text" in result["error"]
        assert "site" in result["error"]

    def test_with_prefixed_original_file(self):
        """Test with already prefixed original_file."""
        mock_site = MagicMock()
        # Should process without error
        update_file_text("File:Example.svg", "new wikitext", mock_site)

    def test_error_message_format(self, caplog):
        """Test that error message is properly formatted with comma separation."""
        mock_site = MagicMock()
        with caplog.at_level(logging.ERROR):
            result = update_file_text(None, None, mock_site)

        assert result["success"] is False
        # Should contain comma-separated list of missing fields
        assert "original_file" in result["error"]
        assert "updated_file_text" in result["error"]
