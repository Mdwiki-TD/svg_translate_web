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
        assert "get_category_members failed" in caplog.text
        assert "Category:Missing" in caplog.text

    def test_logger_debug_called(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """logger.debug is called once with the category title."""
        category = MagicMock()
        category.members.return_value = iter([])
        self._setup_pages(mock_site, category)

        with caplog.at_level("DEBUG"):
            CategoryMembersService(mock_site).get_category_members(category_title="Category:Empty")

        assert "get_category_members for 'Category:Empty'" in caplog.text

    def test_custom_namespace_and_limit(self, mock_site: MagicMock):
        """namespace is forwarded to members(); limit is accepted for backward compatibility and ignored."""
        category = MagicMock()
        category.members.return_value = iter([])
        self._setup_pages(mock_site, category)

        CategoryMembersService(mock_site).get_category_members(category_title="Category:NS14", namespace=14, limit=100)

        category.members.assert_called_once_with(
            prop="ids|title",
            namespace=14,
            sort="sortkey",
            dir="asc",
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
        """APIError triggers logger.exception (the traceback carries the error info)."""
        category = MagicMock()
        category.members.side_effect = mwclient.errors.APIError(
            "api-error-code",
            "read-apierror",
            {},
        )
        self._setup_pages(mock_site, category)

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:Err")

        assert result == []
        mock_logger.exception.assert_called_once()
        args, _ = mock_logger.exception.call_args
        assert "Category:Err" in args[1]

    @patch("src.main_app.api_services.clients.category_members_api.logger")
    def test_logger_exception_on_key_error(self, mock_logger: MagicMock, mock_site: MagicMock):
        """KeyError triggers logger.exception with the category title."""
        pages = MagicMock()
        pages.__getitem__.side_effect = KeyError("bogus-key")
        mock_site.pages = pages

        result = CategoryMembersService(mock_site).get_category_members(category_title="Category:NoKey")

        assert result == []
        mock_logger.exception.assert_called_once()
        args, _ = mock_logger.exception.call_args
        assert "Category:NoKey" in args[1]


# ── fetch_cats_members_api ─────────────────────────────────────────────────────────────


def _page(title: str, ns: int = 0, lastrevid: int | None = None) -> dict:
    page = {"pageid": abs(hash(title)) % 1000, "ns": ns, "title": title}
    if lastrevid is not None:
        page["lastrevid"] = lastrevid
    return page


class TestFetchCatsMembersApi:
    """Tests for CategoryMembersService.fetch_cats_members_api."""

    def test_uses_generator_so_prop_info_applies(self, mock_site: MagicMock):
        """prop= modules are ignored with list=categorymembers; a generator is required."""
        mock_site.get.return_value = {"query": {"pages": []}}

        CategoryMembersService(mock_site).fetch_cats_members_api("Category:Test")

        kwargs = mock_site.get.call_args.kwargs
        assert kwargs["generator"] == "categorymembers"
        assert kwargs["prop"] == "info"
        assert kwargs["gcmlimit"] == "max"
        assert "list" not in kwargs

    def test_adds_category_prefix(self, mock_site: MagicMock):
        mock_site.get.return_value = {"query": {"pages": []}}

        CategoryMembersService(mock_site).fetch_cats_members_api("Test cat")

        assert mock_site.get.call_args.kwargs["gcmtitle"] == "Category:Test cat"

    def test_returns_titles_with_current_revid(self, mock_site: MagicMock):
        """lastrevid is the page's current revision, and ns=0 must survive."""
        mock_site.get.return_value = {
            "query": {
                "pages": [
                    _page("Alpha", ns=0, lastrevid=111),
                    _page("Category:Sub", ns=14, lastrevid=222),
                ]
            }
        }

        result = CategoryMembersService(mock_site).fetch_cats_members_api("Category:Test")

        assert [(m.title, m.ns, m.revid) for m in result] == [
            ("Alpha", 0, 111),
            ("Category:Sub", 14, 222),
        ]

    def test_missing_lastrevid_gives_none(self, mock_site: MagicMock):
        mock_site.get.return_value = {"query": {"pages": [_page("NoRev", ns=0)]}}

        result = CategoryMembersService(mock_site).fetch_cats_members_api("Category:Test")

        assert result[0].revid is None

    def test_ns_filter_keeps_main_namespace(self, mock_site: MagicMock):
        """Regression: ns == 0 used to be coerced to None and filtered away."""
        mock_site.get.return_value = {
            "query": {
                "pages": [
                    _page("Alpha", ns=0, lastrevid=111),
                    _page("Category:Sub", ns=14, lastrevid=222),
                ]
            }
        }

        result = CategoryMembersService(mock_site).fetch_cats_members_api("Category:Test", ns=0)

        assert [m.title for m in result] == ["Alpha"]

    def test_tolerates_formatversion_1_pages_dict(self, mock_site: MagicMock):
        mock_site.get.return_value = {"query": {"pages": {"111": _page("Alpha", ns=0, lastrevid=111)}}}

        result = CategoryMembersService(mock_site).fetch_cats_members_api("Category:Test")

        assert [(m.title, m.revid) for m in result] == [("Alpha", 111)]

    def test_follows_continuation(self, mock_site: MagicMock):
        """Every continuation token must be sent back verbatim."""
        mock_site.get.side_effect = [
            {
                "query": {"pages": [_page("Alpha", lastrevid=1)]},
                "continue": {"gcmcontinue": "page|abc|123", "continue": "gcmcontinue||"},
            },
            {"query": {"pages": [_page("Beta", lastrevid=2)]}},
        ]

        result = CategoryMembersService(mock_site).fetch_cats_members_api("Category:Test")

        assert [m.title for m in result] == ["Alpha", "Beta"]
        assert mock_site.get.call_count == 2
        assert mock_site.get.call_args.kwargs["gcmcontinue"] == "page|abc|123"

    def test_stops_at_max_iterations(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """Advancing-but-endless tokens are capped by MAX_ITERATIONS."""
        counter = iter(range(10_000))

        def endless(*_args, **_kwargs):
            n = next(counter)
            return {
                "query": {"pages": [_page(f"Page{n}", lastrevid=1)]},
                "continue": {"gcmcontinue": f"page|{n}", "continue": "gcmcontinue||"},
            }

        mock_site.get.side_effect = endless

        result = CategoryMembersService(mock_site).fetch_cats_members_api("Category:Big")

        assert mock_site.get.call_count == CategoryMembersService.MAX_ITERATIONS
        assert len(result) == CategoryMembersService.MAX_ITERATIONS
        assert "maximum iterations" in caplog.text

    def test_stops_on_repeated_continuation_token(self, mock_site: MagicMock, caplog: pytest.LogCaptureFixture):
        """A non-advancing token stops after the second request, without duplicates."""
        mock_site.get.return_value = {
            "query": {"pages": [_page("Alpha", lastrevid=1)]},
            "continue": {"gcmcontinue": "page|abc|123", "continue": "gcmcontinue||"},
        }

        result = CategoryMembersService(mock_site).fetch_cats_members_api("Category:Big")

        assert mock_site.get.call_count == 2
        assert [m.title for m in result] == ["Alpha"]
        assert "did not advance" in caplog.text

    def test_ns_filter_is_sent_to_the_server(self, mock_site: MagicMock):
        mock_site.get.return_value = {"query": {"pages": []}}

        CategoryMembersService(mock_site).fetch_cats_members_api("Category:Test", ns=0)

        assert mock_site.get.call_args.kwargs["gcmnamespace"] == 0

    def test_request_error_returns_partial_or_raises(self, mock_site: MagicMock):
        first = {
            "query": {"pages": [_page("Alpha", lastrevid=1)]},
            "continue": {"gcmcontinue": "t", "continue": "gcmcontinue||"},
        }
        error = mwclient.errors.APIError("code", "info", {})
        service = CategoryMembersService(mock_site)

        mock_site.get.side_effect = [first, error]
        assert [m.title for m in service.fetch_cats_members_api("Category:Test")] == ["Alpha"]

        mock_site.get.side_effect = [first, error]
        with pytest.raises(mwclient.errors.APIError):
            service.fetch_cats_members_api("Category:Test", raise_on_error=True)
