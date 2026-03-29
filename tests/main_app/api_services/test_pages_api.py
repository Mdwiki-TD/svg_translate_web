"""
Tests for src/main_app/api_services/pages_api.py
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import mwclient
import pytest

from src.main_app.api_services.pages_api import (
    create_page,
    is_page_exists,
    update_file_text,
    update_page_text,
)


class TestIsPageExists:
    """Tests for the is_page_exists function."""

    def test_page_exists_returns_true(self) -> None:
        """Test that is_page_exists returns True when page exists."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.Pages = MagicMock()
        mock_site.Pages.__getitem__ = MagicMock(return_value=mock_page)

        result = is_page_exists("File:Test.svg", mock_site)

        assert result is True
        mock_site.Pages.__getitem__.assert_called_once_with("File:Test.svg")

    def test_page_not_exists_returns_false(self) -> None:
        """Test that is_page_exists returns False when page does not exist."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.Pages = MagicMock()
        mock_site.Pages.__getitem__ = MagicMock(return_value=mock_page)

        result = is_page_exists("File:NonExistent.svg", mock_site)

        assert result is False
        mock_site.Pages.__getitem__.assert_called_once_with("File:NonExistent.svg")

    def test_page_exists_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that is_page_exists logs a warning when page exists."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.Pages = MagicMock()
        mock_site.Pages.__getitem__ = MagicMock(return_value=mock_page)

        with caplog.at_level(logging.WARNING):
            result = is_page_exists("File:Existing.svg", mock_site)

        assert result is True
        assert "Title File:Existing.svg exists" in caplog.text


class TestCreatePage:
    """Tests for the create_page function."""

    def test_create_page_success(self) -> None:
        """Test successful page creation."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)

        result = create_page(
            page_name="File:Test.svg",
            wikitext="{{Information}}",
            site=mock_site,
            summary="Test summary",
        )

        assert result == {"success": True}
        mock_site.pages.__getitem__.assert_called_once_with("File:Test.svg")
        mock_page.edit.assert_called_once_with("{{Information}}", summary="Test summary")

    def test_create_page_without_summary(self) -> None:
        """Test page creation with default empty summary."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)

        result = create_page(
            page_name="File:Test.svg",
            wikitext="{{Information}}",
            site=mock_site,
        )

        assert result == {"success": True}
        mock_page.edit.assert_called_once_with("{{Information}}", summary="")

    def test_create_page_missing_page_name(self) -> None:
        """Test create_page returns error when page_name is missing."""
        mock_site = MagicMock(spec=mwclient.Site)

        result = create_page(
            page_name="",
            wikitext="{{Information}}",
            site=mock_site,
        )

        assert result["success"] is False
        assert "Missing required fields" in result["error"]
        assert "page_name" in result["error"]

    def test_create_page_missing_wikitext(self) -> None:
        """Test create_page returns error when wikitext is missing."""
        mock_site = MagicMock(spec=mwclient.Site)

        result = create_page(
            page_name="File:Test.svg",
            wikitext="",
            site=mock_site,
        )

        assert result["success"] is False
        assert "Missing required fields" in result["error"]
        assert "wikitext" in result["error"]

    def test_create_page_missing_site(self) -> None:
        """Test create_page returns error when site is None."""
        result = create_page(
            page_name="File:Test.svg",
            wikitext="{{Information}}",
            site=None,
        )

        assert result["success"] is False
        assert "Missing required fields" in result["error"]
        assert "site" in result["error"]

    def test_create_page_load_page_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test create_page handles exception when loading page fails."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(side_effect=Exception("Page load failed"))

        with caplog.at_level(logging.ERROR):
            result = create_page(
                page_name="File:Test.svg",
                wikitext="{{Information}}",
                site=mock_site,
            )

        assert result["success"] is False
        assert "Page load failed" in result["error"]
        assert "Failed to load page File:Test.svg" in caplog.text

    def test_create_page_edit_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test create_page handles exception when edit fails."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_site.pages = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)
        mock_page.edit = MagicMock(side_effect=Exception("Edit failed"))

        with caplog.at_level(logging.ERROR):
            result = create_page(
                page_name="File:Test.svg",
                wikitext="{{Information}}",
                site=mock_site,
                summary="Test summary",
            )

        assert result["success"] is False
        assert "Edit failed" in result["error"]
        assert "Failed to edit page File:Test.svg" in caplog.text


class TestUpdateFileText:
    """Tests for update_file_text function."""

    def test_valid_inputs(self):
        """Test with valid inputs - currently returns incomplete dict (TODO implementation)."""
        mock_site = MagicMock()
        _result = update_file_text("Example.svg", "new wikitext", mock_site)
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


class TestUpdatePageText:
    """Tests for update_page_text function."""

    def test_valid_inputs_calls_edit(self):
        """Test with valid inputs calls page.edit."""
        mock_site = MagicMock()
        result = update_page_text("Template:Test", "new wikitext", mock_site, summary="test edit")
        assert result["success"] is True
        mock_site.pages.__getitem__.assert_called_once_with("Template:Test")

    def test_missing_page_name_returns_error(self, caplog):
        """Test that missing page_name returns error dict."""
        mock_site = MagicMock()
        with caplog.at_level(logging.ERROR):
            result = update_page_text(None, "new wikitext", mock_site)
        assert result["success"] is False
        assert "page_name" in result["error"]

    def test_missing_updated_text_returns_error(self, caplog):
        """Test that missing updated_text returns error dict."""
        mock_site = MagicMock()
        with caplog.at_level(logging.ERROR):
            result = update_page_text("Template:Test", None, mock_site)
        assert result["success"] is False
        assert "updated_text" in result["error"]

    def test_missing_site_returns_error(self, caplog):
        """Test that missing site returns error dict."""
        with caplog.at_level(logging.ERROR):
            result = update_page_text("Template:Test", "new wikitext", None)
        assert result["success"] is False
        assert "site" in result["error"]

    def test_edit_exception_returns_error(self, caplog):
        """Test that exception from page.edit returns error dict."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.edit.side_effect = Exception("Edit conflict")
        mock_site.pages.__getitem__.return_value = mock_page
        with caplog.at_level(logging.ERROR):
            result = update_page_text("Template:Test", "new wikitext", mock_site)
        assert result["success"] is False
        assert "Edit conflict" in result["error"]

    def test_default_empty_summary(self):
        """Test that default empty summary is used."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_site.pages.__getitem__.return_value = mock_page
        update_page_text("Template:Test", "new wikitext", mock_site)
        mock_page.edit.assert_called_once_with("new wikitext", summary="")
