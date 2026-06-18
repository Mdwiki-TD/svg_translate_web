"""Unit tests for src/main_app/api_services/category.py module.

Functions to test: get_category_members
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import mwclient.errors
import pytest

from src.main_app.api_services.category import get_category_members

# ── Helpers ────────────────────────────────────────────────────────────────────────────


def _make_page(name: str) -> MagicMock:
    page = MagicMock()
    page.name = name
    return page


# ── Tests ──────────────────────────────────────────────────────────────────────────────


class TestGetCategoryMembers:
    """Tests for get_category_members()."""

    @staticmethod
    def _setup_pages(mock_site: MagicMock, category: MagicMock) -> None:
        """Helper: wire mock_site.pages as a MagicMock returning *category* on lookup."""
        pages = MagicMock()
        pages.__getitem__.return_value = category
        mock_site.pages = pages

    def test_successful_retrieval(self, mock_site: MagicMock):
        """Happy path: members() returns page objects → list of names."""
        expected = ["File:Alpha.svg", "File:Beta.svg", "File:Gamma.svg"]
        members_iter = iter(_make_page(n) for n in expected)

        category = MagicMock()
        category.members.return_value = members_iter
        self._setup_pages(mock_site, category)

        result = get_category_members(mock_site, "Category:Test cat")

        assert result == expected
        category.members.assert_called_once_with(
            prop="ids|title",
            namespace=0,
            sort="sortkey",
            dir="asc",
            start=None,
            end=None,
            generator=True,
        )

    def test_mixed_string_and_object_members(self, mock_site: MagicMock):
        """Members list may contain plain strings or page objects with .name."""
        obj_a = _make_page("File:ObjA.svg")
        obj_b = _make_page("File:ObjB.svg")
        members_iter = iter(["File:StrA.svg", obj_a, obj_b])

        category = MagicMock()
        category.members.return_value = members_iter
        self._setup_pages(mock_site, category)

        result = get_category_members(mock_site, "Category:Mixed")

        assert result == ["File:StrA.svg", "File:ObjA.svg", "File:ObjB.svg"]

    def test_api_error_on_members(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """members() raises APIError → function returns [] and logs a warning."""
        category = MagicMock()
        category.members.side_effect = mwclient.errors.APIError(
            "cat-member-fetch-failed",
            "read-apierror",
            {},
        )
        self._setup_pages(mock_site, category)

        result = get_category_members(mock_site, "Category:Broken")

        assert result == []
        assert "cat-member-fetch-failed" in caplog.text
        assert "Category:Broken" in caplog.text

    def test_key_error_on_page_lookup(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """Accessing site.pages[title] raises KeyError → returns [] and logs a warning."""
        pages = MagicMock()
        pages.__getitem__.side_effect = KeyError("Category:Missing")
        mock_site.pages = pages

        result = get_category_members(mock_site, "Category:Missing")

        assert result == []
        assert "Key error" in caplog.text
        assert "Category:Missing" in caplog.text

    def test_logger_debug_called(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """logger.debug is called once with the category title."""
        category = MagicMock()
        category.members.return_value = iter([])
        self._setup_pages(mock_site, category)

        with caplog.at_level("DEBUG"):
            get_category_members(mock_site, "Category:Empty")

        assert "load category members for Category:Empty" in caplog.text

    def test_custom_namespace_and_limit(self, mock_site: MagicMock):
        """namespace and limit parameters are forwarded to members()."""
        category = MagicMock()
        category.members.return_value = iter([])
        self._setup_pages(mock_site, category)

        get_category_members(mock_site, "Category:NS14", namespace=14, limit=100)

        category.members.assert_called_once_with(
            prop="ids|title",
            namespace=14,
            sort="sortkey",
            dir="asc",
            start=None,
            end=None,
            generator=True,
        )

    def test_empty_category(self, mock_site: MagicMock):
        """An empty category returns an empty list."""
        category = MagicMock()
        category.members.return_value = iter([])
        self._setup_pages(mock_site, category)

        result = get_category_members(mock_site, "Category:Empty")

        assert result == []

    @patch("src.main_app.api_services.category.logger")
    def test_logger_exception_on_api_error(self, mock_logger: MagicMock, mock_site: MagicMock):
        """APIError triggers logger.warning with the error info."""
        category = MagicMock()
        category.members.side_effect = mwclient.errors.APIError(
            "api-error-code",
            "read-apierror",
            {},
        )
        self._setup_pages(mock_site, category)

        result = get_category_members(mock_site, "Category:Err")

        assert result == []
        mock_logger.warning.assert_called_once()
        args, _ = mock_logger.warning.call_args
        assert "api-error-code" in args[0]

    @patch("src.main_app.api_services.category.logger")
    def test_logger_exception_on_key_error(self, mock_logger: MagicMock, mock_site: MagicMock):
        """KeyError triggers logger.warning with the error message."""
        pages = MagicMock()
        pages.__getitem__.side_effect = KeyError("bogus-key")
        mock_site.pages = pages

        result = get_category_members(mock_site, "Category:NoKey")

        assert result == []
        mock_logger.warning.assert_called_once()
        args, _ = mock_logger.warning.call_args
        assert "bogus-key" in args[0]
