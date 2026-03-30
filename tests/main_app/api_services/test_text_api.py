"""Tests for text_api module."""

import logging
from unittest.mock import MagicMock

from src.main_app.api_services.text_api import get_file_text, get_page_text


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


class TestGetPageText:
    """Tests for get_page_text function."""

    def _create_mock_site(self, text_content=""):
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.text.return_value = text_content
        mock_site.pages.__getitem__.return_value = mock_page
        return mock_site

    def test_valid_inputs_returns_text(self):
        """Test with valid inputs returns the page text."""
        mock_site = self._create_mock_site(text_content="Template wikitext")
        result = get_page_text("Template:OWID/Barley yields", mock_site)
        assert result == "Template wikitext"
        mock_site.pages.__getitem__.assert_called_once_with("Template:OWID/Barley yields")

    def test_does_not_add_file_prefix(self):
        """Test that no File: prefix is added to the page name."""
        mock_site = self._create_mock_site(text_content="content")
        get_page_text("Template:OWID/Test", mock_site)
        mock_site.pages.__getitem__.assert_called_once_with("Template:OWID/Test")

    def test_missing_page_name_returns_empty_string(self, caplog):
        """Test that missing page_name returns empty string."""
        mock_site = self._create_mock_site()
        with caplog.at_level(logging.ERROR):
            result = get_page_text(None, mock_site)
        assert result == ""
        assert "Missing required fields for get_page_text" in caplog.text

    def test_missing_site_returns_empty_string(self, caplog):
        """Test that missing site returns empty string."""
        with caplog.at_level(logging.ERROR):
            result = get_page_text("Template:Test", None)
        assert result == ""
        assert "Missing required fields for get_page_text" in caplog.text

    def test_site_exception_returns_empty_string(self, caplog):
        """Test that exception from site returns empty string."""
        mock_site = MagicMock()
        mock_site.pages.__getitem__.side_effect = Exception("Connection error")
        with caplog.at_level(logging.ERROR):
            result = get_page_text("Template:Test", mock_site)
        assert result == ""
        assert "Failed to retrieve wikitext" in caplog.text
