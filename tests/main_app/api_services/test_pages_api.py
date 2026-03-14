"""
Tests for src/main_app/api_services/pages_api.py
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import mwclient
import pytest

from src.main_app.api_services.pages_api import (
    create_page,
    is_page_exists,
)


class TestIsPageExists:
    """Tests for the is_page_exists function."""

    def test_page_exists_returns_true(self) -> None:
        """Test that is_page_exists returns True when page exists."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.Pages.__getitem__ = MagicMock(return_value=mock_page)

        result = is_page_exists("File:Test.svg", mock_site)

        assert result is True
        mock_site.Pages.__getitem__.assert_called_once_with("File:Test.svg")

    def test_page_not_exists_returns_false(self) -> None:
        """Test that is_page_exists returns False when page does not exist."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.Pages.__getitem__ = MagicMock(return_value=mock_page)

        result = is_page_exists("File:NonExistent.svg", mock_site)

        assert result is False
        mock_site.Pages.__getitem__.assert_called_once_with("File:NonExistent.svg")

    def test_page_exists_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that is_page_exists logs a warning when page exists."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.Pages.__getitem__ = MagicMock(return_value=mock_page)

        with caplog.at_level(logging.WARNING):
            result = is_page_exists("File:Existing.svg", mock_site)

        assert result is True
        assert "File Existing.svg already exists on Commons" in caplog.text


class TestCreatePage:
    """Tests for the create_page function."""

    def test_create_page_success(self) -> None:
        """Test successful page creation."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
        mock_site.pages.__getitem__ = MagicMock(return_value=mock_page)

        result = create_page(
            page_name="File:Test.svg",
            wikitext="{{Information}}",
            site=mock_site,
            summary="Test summary",
        )

        assert result == {"success": True}
        mock_site.pages.__getitem__.assert_called_once_with("File:Test.svg")
        mock_page.edit.assert_called_once_with(
            "{{Information}}", summary="Test summary"
        )

    def test_create_page_without_summary(self) -> None:
        """Test page creation with default empty summary."""
        mock_site = MagicMock(spec=mwclient.Site)
        mock_page = MagicMock()
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
        assert "Failed to create page File:Test.svg" in caplog.text
