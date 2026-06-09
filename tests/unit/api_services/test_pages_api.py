"""
Tests for src/main_app/api_services/pages_api.py
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.pages_api import (
    create_page,
    is_page_exists,
    update_page_text,
)

@pytest.fixture
def mock_site_not_exists_pages(mock_site_pages):
    return mock_site_pages(False)

class TestIsPageExists:
    """Tests for the is_page_exists function."""

    def test_page_exists_returns_true(self, mock_site_pages) -> None:
        """Test that is_page_exists returns True when page exists."""
        _site =  mock_site_pages(True)
        result = is_page_exists("File:Test.svg", _site)

        assert result is True
        _site.pages.__getitem__.assert_called_once_with("File:Test.svg")

    def test_page_not_exists_returns_false(self, mock_site_not_exists_pages) -> None:
        """Test that is_page_exists returns False when page does not exist."""

        result = is_page_exists("File:NonExistent.svg", mock_site_not_exists_pages)

        assert result is False
        mock_site_not_exists_pages.pages.__getitem__.assert_called_once_with("File:NonExistent.svg")

    def test_page_exists_logs_info(self, caplog: pytest.LogCaptureFixture, mock_site_pages) -> None:
        """Test that is_page_exists logs a info when page exists."""
        _site =  mock_site_pages(True)
        with caplog.at_level(logging.INFO):
            result = is_page_exists("File:Existing.svg", _site)

        assert result is True
        assert "Page 'File:Existing.svg' exists" in caplog.text

    def test_page_not_exists_logs_warning(self, caplog: pytest.LogCaptureFixture, mock_site_not_exists_pages) -> None:
        """Test that is_page_exists logs a warning when page not exists."""

        with caplog.at_level(logging.WARNING):
            result = is_page_exists("File:Not-existing.svg", mock_site_not_exists_pages)

        assert result is False
        assert "Page 'File:Not-existing.svg' does not exist" in caplog.text


class TestCreatePage:
    """Tests for the create_page function."""

    def test_create_page_success(self, mock_site_not_exists_pages, mock_page) -> None:
        """Test successful page creation."""

        result = create_page(
            page_name="File:Test.svg",
            wikitext="{{Information}}",
            site=mock_site_not_exists_pages,
            summary="Test summary",
        )

        assert result == {"success": True}
        mock_site_not_exists_pages.pages.__getitem__.assert_called_once_with("File:Test.svg")
        mock_page.edit.assert_called_once_with("{{Information}}", summary="Test summary", createonly=True)

    def test_create_page_without_summary(self, mock_site_not_exists_pages, mock_page) -> None:
        """Test page creation with default empty summary."""

        result = create_page(
            page_name="File:Test.svg",
            wikitext="{{Information}}",
            site=mock_site_not_exists_pages,
        )

        assert result == {"success": True}
        mock_page.edit.assert_called_once_with("{{Information}}", summary="", createonly=True)

    def test_create_page_missing_page_name(self, mock_site) -> None:
        """Test create_page returns error when page_name is missing."""

        result = create_page(
            page_name="",
            wikitext="{{Information}}",
            site=mock_site,
        )

        assert result["success"] is False
        assert "Missing required fields" in result["error"]
        assert "page_name" in result["error"]

    def test_create_page_missing_wikitext(self, mock_site) -> None:
        """Test create_page returns error when wikitext is missing."""

        result = create_page(
            page_name="File:Test.svg",
            wikitext="",
            site=mock_site,
        )

        assert result["success"] is False
        assert "Missing required fields" in result["error"]
        assert "wikitext" in result["error"]

    def test_create_page_missing_site(self, mock_site) -> None:
        """Test create_page returns error when site is None."""
        result = create_page(
            page_name="File:Test.svg",
            wikitext="{{Information}}",
            site=None,
        )

        assert result["success"] is False
        assert "Missing required fields" in result["error"]
        assert "site" in result["error"]

    def test_create_page_load_page_exception(self, caplog: pytest.LogCaptureFixture, mock_site) -> None:
        """Test create_page handles exception when loading page fails."""

        mock_site.pages.__getitem__ = MagicMock(side_effect=Exception("Page load failed"))

        with caplog.at_level(logging.ERROR):
            result = create_page(
                page_name="File:Test.svg",
                wikitext="{{Information}}",
                site=mock_site,
            )

        assert result["success"] is False
        assert "Page load failed" in result["error"]
        assert "Failed to load page 'File:Test.svg'" in caplog.text

    def test_create_page_edit_exception(
        self, caplog: pytest.LogCaptureFixture, mock_site_not_exists_pages, mock_page
    ) -> None:
        """Test create_page handles exception when edit fails."""

        mock_page.edit = MagicMock(side_effect=Exception("Edit failed"))

        with caplog.at_level(logging.ERROR):
            result = create_page(
                page_name="File:Test.svg",
                wikitext="{{Information}}",
                site=mock_site_not_exists_pages,
                summary="Test summary",
            )

        assert result["success"] is False
        assert "Edit failed" in result["error"]
        assert "Failed to edit page 'File:Test.svg'" in caplog.text


class TestUpdatePageText:
    """Tests for update_page_text function."""

    def test_valid_inputs_calls_edit(self, mock_site):
        """Test with valid inputs calls page.edit."""

        result = update_page_text("Template:Test", "new wikitext", mock_site, summary="test edit")
        assert result["success"] is True
        mock_site.pages.__getitem__.assert_called_once_with("Template:Test")

    def test_missing_page_name_returns_error(self, caplog, mock_site):
        """Test that missing page_name returns error dict."""

        with caplog.at_level(logging.ERROR):
            result = update_page_text(None, "new wikitext", mock_site)
        assert result["success"] is False
        assert "page_name" in result["error"]

    def test_missing_updated_text_returns_error(self, caplog, mock_site):
        """Test that missing updated_text returns error dict."""

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

    def test_edit_exception_returns_error(self, caplog, mock_site_not_exists_pages, mock_page):
        """Test that exception from page.edit returns error dict."""

        mock_page.edit.side_effect = Exception("Edit conflict")
        with caplog.at_level(logging.ERROR):
            result = update_page_text("Template:Test", "new wikitext", mock_site_not_exists_pages)
        assert result["success"] is False
        assert "Edit conflict" in result["error"]

    def test_default_empty_summary(self, mock_site_not_exists_pages, mock_page):
        """Test that default empty summary is used."""
        update_page_text("Template:Test", "new wikitext", mock_site_not_exists_pages)
        mock_page.edit.assert_called_once_with("new wikitext", summary="", nocreate=True)
