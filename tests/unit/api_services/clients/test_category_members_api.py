"""
Unit tests for category.py module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import mwclient.errors
import pytest
from src.main_app.api_services.clients.category_members_api import CategoryMembersService

# ── Helpers ────────────────────────────────────────────────────────────────────────────


def _make_page(name: str) -> MagicMock:
    page = MagicMock()
    page.name = name
    return page


# ── Tests ──────────────────────────────────────────────────────────────────────────────


class TestGetCategoryMembers:
    """Tests for CategoryMembersService.get_category_members."""

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

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:Test cat")

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

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:Mixed")

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

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:Broken")

        assert result == []
        assert "cat-member-fetch-failed" in caplog.text
        assert "Category:Broken" in caplog.text

    def test_key_error_on_page_lookup(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """Accessing site.pages[title] raises KeyError → returns [] and logs a warning."""
        pages = MagicMock()
        pages.__getitem__.side_effect = KeyError("Category:Missing")
        mock_site.pages = pages

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:Missing")

        assert result == []
        assert "Key error" in caplog.text
        assert "Category:Missing" in caplog.text

    def test_logger_debug_called(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """logger.debug is called once with the category title."""
        category = MagicMock()
        category.members.return_value = iter([])
        self._setup_pages(mock_site, category)

        with caplog.at_level("DEBUG"):
            CategoryMembersService(mock_site).get_category_members(category_title="Category:Empty")

        assert "load category members for Category:Empty" in caplog.text

    def test_custom_namespace_and_limit(self, mock_site: MagicMock):
        """namespace and limit parameters are forwarded to members()."""
        category = MagicMock()
        category.members.return_value = iter([])
        self._setup_pages(mock_site, category)

        CategoryMembersService(mock_site).get_category_members(category_title="Category:NS14", namespace=14, limit=100)

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

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:Empty")

        assert result == []

    @patch("src.main_app.api_services.clients.category_members_api.logger")
    def test_logger_exception_on_api_error(self, mock_logger: MagicMock, mock_site: MagicMock):
        """APIError triggers logger.warning with the error info."""
        category = MagicMock()
        category.members.side_effect = mwclient.errors.APIError(
            "api-error-code",
            "read-apierror",
            {},
        )
        self._setup_pages(mock_site, category)

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:Err")

        assert result == []
        mock_logger.warning.assert_called_once()
        args, _ = mock_logger.warning.call_args
        assert "api-error-code" in args[0]

    @patch("src.main_app.api_services.clients.category_members_api.logger")
    def test_logger_exception_on_key_error(self, mock_logger: MagicMock, mock_site: MagicMock):
        """KeyError triggers logger.warning with the error message."""
        pages = MagicMock()
        pages.__getitem__.side_effect = KeyError("bogus-key")
        mock_site.pages = pages

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:NoKey")

        assert result == []
        mock_logger.warning.assert_called_once()
        args, _ = mock_logger.warning.call_args
        assert "bogus-key" in args[0]


class TestGetCategoryMembersTitles:
    def test_returns_titles(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "categorymembers": [
                    {"title": "File:A.svg"},
                    {"title": "File:B.svg"},
                ]
            }
        }
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Test")
        assert result == ["File:A.svg", "File:B.svg"]

    def test_empty_category(self, mock_site):
        mock_site.get.return_value = {"query": {"categorymembers": []}}
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Empty")
        assert result == []

    def test_pagination(self, mock_site):
        mock_site.get.side_effect = [
            {
                "query": {"categorymembers": [{"title": "File:A.svg"}]},
                "continue": {"cmcontinue": "nextpage"},
            },
            {
                "query": {"categorymembers": [{"title": "File:B.svg"}]},
            },
        ]
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Test")
        assert result == ["File:A.svg", "File:B.svg"]
        assert mock_site.get.call_count == 2

    def test_invalid_category(self, mock_site):
        from mwclient.errors import APIError

        mock_site.get.side_effect = APIError("invalidcategory", "Invalid category", {})
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Invalid")
        assert result == []

    def test_retry_on_first_request_exits_loop(self, mock_site, monkeypatch):
        """First-request exception exits while loop (first_request=False, cmcontinue=None)."""
        monkeypatch.setattr("src.main_app.api_services.query_api.time.sleep", lambda s: None)
        mock_site.get.side_effect = Exception("Timeout error")
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Test")
        assert result == []

    def test_retry_on_continuation(self, mock_site, monkeypatch):
        monkeypatch.setattr("src.main_app.api_services.query_api.time.sleep", lambda s: None)
        mock_site.get.side_effect = [
            {
                "query": {"categorymembers": [{"title": "File:A.svg"}]},
                "continue": {"cmcontinue": "next|page"},
            },
            Exception("Timeout error"),
            {
                "query": {"categorymembers": [{"title": "File:B.svg"}]},
            },
        ]
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Test")
        assert result == ["File:A.svg", "File:B.svg"]

    def test_namespace_file(self, mock_site):
        mock_site.get.return_value = {
            "query": {"categorymembers": [{"title": "File:A.svg"}]},
        }
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Test", namespace=6)
        assert result == ["File:A.svg"]

    def test_namespace_subcat(self, mock_site):
        mock_site.get.return_value = {
            "query": {"categorymembers": [{"title": "Category:Sub"}]},
        }
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Test", namespace=14)
        assert result == ["Category:Sub"]

    def test_namespace_other(self, mock_site):
        mock_site.get.return_value = {
            "query": {"categorymembers": [{"title": "Template:Test"}]},
        }
        service = CategoryMembersService(site=mock_site)
        result = service.get_category_members_titles("Category:Test", namespace=10)
        assert result == ["Template:Test"]
