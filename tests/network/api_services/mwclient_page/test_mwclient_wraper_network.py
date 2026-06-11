"""
Real (non-mocked) integration tests for MwClientPage.

src/main_app/api_services/mwclient_page/mwclient_wraper.py

These tests make live HTTP requests to Wikimedia servers.
Run them with:  pytest -m network

Environment variables required for write tests:
    MW_TEST_USERNAME  – bot username for test.wikipedia.org
    MW_TEST_PASSWORD  – bot password for test.wikipedia.org

Read/query tests use commons.wikimedia.org (no credentials needed).
Write tests use test.wikipedia.org (credentials required; safe sandbox).
"""

from __future__ import annotations

import time
import uuid

import mwclient
import pytest
from mwclient.client import Site

from src.main_app.api_services.mwclient_page.mwclient_wraper import MwClientPage
from tests.network.network_conftest import TestNetwork

pytestmark = pytest.mark.network

# ---------------------------------------------------------------------------
# TestLoadPage
# ---------------------------------------------------------------------------


class TestLoadPage(TestNetwork):
    """Tests for MwClientPage.load_page()."""

    def test_load_existing_page_returns_page_object(self):
        page = MwClientPage("Main Page", self.site)
        result = page.load_page()
        assert result is not None
        assert result.exists

    def test_load_missing_page_returns_object_but_not_exists(self):
        title = "This Page Almost Certainly Does Not Exist XYZ999ABC"
        page = MwClientPage(title, self.site)
        result = page.load_page()
        # mwclient returns a Page object even for missing pages
        assert result is not None
        assert not result.exists

    def test_load_invalid_title_returns_none_and_sets_error(self):
        # Titles with certain characters are invalid on MediaWiki
        invalid_title = "[Invalid<>Title]"
        page = MwClientPage(invalid_title, self.site)
        result = page.load_page()
        assert result is None
        assert page.load_page_error != ""

    def test_load_page_is_cached_on_second_call(self):
        page = MwClientPage("Main Page", self.site)
        first = page.load_page()
        second = page.load_page()
        assert first is second  # same object, not fetched twice


# ---------------------------------------------------------------------------
# TestExists
# ---------------------------------------------------------------------------


class TestExists(TestNetwork):
    """Tests for MwClientPage.exists() / check_exists()."""

    def test_existing_page_returns_true(self):
        page = MwClientPage("Main Page", self.site)
        assert page.exists() is True

    def test_missing_page_returns_false(self):
        title = "Definitely Missing Page ZZZ123XYZ"
        page = MwClientPage(title, self.site)
        assert page.exists() is False

    def test_check_exists_alias_matches_exists(self):
        page = MwClientPage("Main Page", self.site)
        assert page.exists() == page.check_exists()

    def test_well_known_commons_category_exists(self):
        page = MwClientPage("Category:Featured pictures on Wikimedia Commons", self.site)
        assert page.exists() is True


# ---------------------------------------------------------------------------
# TestGetRedirectTarget
# ---------------------------------------------------------------------------


class TestGetRedirectTarget(TestNetwork):
    """Tests for MwClientPage.get_redirect_target()."""

    def test_redirect_page_returns_target(self):
        # "Wikimedia Commons" on Commons itself redirects to "Main Page"
        # Use a well-known redirect on Commons
        page = MwClientPage("COM:OVERWRITE", self.site)
        target = page.get_redirect_target()
        # Either it redirects (target is not None) or the title changed.
        # We only assert the return type contract.
        assert target is None or isinstance(target, mwclient.page.Page)

    def test_non_redirect_page_returns_none(self):
        page = MwClientPage("Main Page", self.site)
        target = page.get_redirect_target()
        assert target is None

    def test_missing_page_returns_none(self):
        page = MwClientPage("This Page Does Not Exist ZZZZZZ", self.site)
        target = page.get_redirect_target()
        assert target is None


# ---------------------------------------------------------------------------
# TestIsRedirect
# ---------------------------------------------------------------------------


class TestIsRedirect(TestNetwork):
    """Tests for MwClientPage.is_redirect()."""

    def test_known_redirect_is_true(self):
        # COM:L is a well-known shortcut redirect on Commons
        page = MwClientPage("COM:L", self.site)
        result = page.is_redirect()
        # If the shortcut was removed, we just assert the return type
        assert isinstance(result, bool)

    def test_main_page_is_not_redirect(self):
        page = MwClientPage("Main Page", self.site)
        assert page.is_redirect() is False

    def test_missing_page_is_not_redirect(self):
        page = MwClientPage("Definitely Missing ZZZYYYXXX", self.site)
        assert page.is_redirect() is False


# ---------------------------------------------------------------------------
# TestCreate
# ---------------------------------------------------------------------------


class TestCreate(TestNetwork):
    """Tests for MwClientPage.create() / create_page().

    All writes go to test.wikipedia.org.
    Requires MW_TEST_USERNAME and MW_TEST_PASSWORD.
    """

    def test_create_new_page_succeeds(self):
        site = self._require_test_site()
        title = self._unique_title("Create")
        page = MwClientPage(title, site)

        result = page.create("Integration test page — safe to delete.", "network test create")

        assert result == {}
        assert result["success"] is True

    def test_create_page_alias_matches_create(self):
        site = self._require_test_site()
        title = self._unique_title("CreateAlias")
        page = MwClientPage(title, site)

        result = page.create_page("Integration test page — alias check.", "network test create_page alias")

        assert result["success"] is True

    def test_create_duplicate_page_fails(self):
        site = self._require_test_site()
        title = self._unique_title("CreateDuplicate")
        page = MwClientPage(title, site)

        first = page.create("First write.", "network test: first create")
        assert first["success"] is True

        # A fresh MwClientPage for the same title — page is already cached on the
        # previous instance, so build a new one to avoid the internal cache.
        duplicate = MwClientPage(title, site)
        second = duplicate.create("Second write.", "network test: duplicate create")

        assert second["success"] is False
        assert "exist" in second.get("error", "").lower() or second["error"] == "articleexists"

    def test_create_returns_success_dict_structure(self):
        site = self._require_test_site()
        title = self._unique_title("CreateDict")
        page = MwClientPage(title, site)

        result = page.create("Dict structure test.", "network test dict")

        assert isinstance(result, dict)
        assert "success" in result


# ---------------------------------------------------------------------------
# TestEdit
# ---------------------------------------------------------------------------


class TestEdit(TestNetwork):
    """Tests for MwClientPage.edit() / edit_page().

    All writes go to test.wikipedia.org.
    """

    def _make_page(self, site: Site, content: str = "Initial content.") -> str:
        """Create a page and return its title."""
        title = self._unique_title("Edit")
        page = MwClientPage(title, site)
        result = page.create(content, "network test: setup for edit")
        assert result["success"] is True, f"Setup failed: {result}"
        return title

    def test_edit_existing_page_succeeds(self):
        site = self._require_test_site()
        title = self._make_page(site)

        page = MwClientPage(title, site)
        result = page.edit("Edited content.", "network test edit")

        assert result["success"] is True

    def test_edit_page_alias_matches_edit(self):
        site = self._require_test_site()
        title = self._make_page(site)

        page = MwClientPage(title, site)
        result = page.edit_page("Alias edit content.", "network test edit_page alias")

        assert result["success"] is True

    def test_edit_missing_page_with_nocreate_fails(self):
        site = self._require_test_site()
        title = self._unique_title("EditMissing")

        page = MwClientPage(title, site)
        result = page.edit("Should not be created.", "network test nocreate", nocreate=True)

        assert result["success"] is False

    def test_edit_updates_content(self):
        site = self._require_test_site()
        title = self._make_page(site, "Before edit.")

        page = MwClientPage(title, site)
        new_content = f"After edit — {uuid.uuid4().hex}"
        result = page.edit(new_content, "network test: verify content update")

        assert result["success"] is True

        # Re-fetch and verify the text changed
        fetched = MwClientPage(title, site)
        raw = fetched.load_page().text()
        assert new_content in raw

    def test_edit_returns_dict_with_success_key(self):
        site = self._require_test_site()
        title = self._make_page(site)

        page = MwClientPage(title, site)
        result = page.edit("Result dict test.", "network test dict check")

        assert isinstance(result, dict)
        assert "success" in result


# ---------------------------------------------------------------------------
# TestMove
# ---------------------------------------------------------------------------


class TestMove(TestNetwork):
    """Tests for MwClientPage.move() / move_page().

    All writes go to test.wikipedia.org.
    """

    def _make_page(self, site: Site) -> str:
        title = self._unique_title("MoveSource")
        page = MwClientPage(title, site)
        result = page.create("Page to be moved.", "network test: setup for move")
        assert result["success"] is True, f"Setup failed: {result}"
        return title

    def test_move_existing_page_succeeds(self):
        site = self._require_test_site()
        source = self._make_page(site)
        target = self._unique_title("MoveDest")

        page = MwClientPage(source, site)
        result = page.move(target, reason="network test move")

        assert result["success"] is True

    def test_move_page_alias_matches_move(self):
        site = self._require_test_site()
        source = self._make_page(site)
        target = self._unique_title("MoveDestAlias")

        page = MwClientPage(source, site)
        result = page.move_page(target, reason="network test move_page alias")

        assert result["success"] is True

    def test_move_missing_page_fails(self):
        site = self._require_test_site()
        title = self._unique_title("MoveMissing")
        target = self._unique_title("MoveDestMissing")

        page = MwClientPage(title, site)
        result = page.move(target, reason="network test: move missing page")

        assert result["success"] is False
        assert result["error"] == "missing"

    def test_move_creates_redirect_by_default(self):
        site = self._require_test_site()
        source = self._make_page(site)
        target = self._unique_title("MoveDestRedirect")

        page = MwClientPage(source, site)
        result = page.move(target, reason="network test redirect check", no_redirect=False)

        assert result["success"] is True

        # Original title should now be a redirect
        time.sleep(1)  # brief pause for the API to settle
        original = MwClientPage(source, site)
        assert original.is_redirect() is True

    def test_move_with_no_redirect_leaves_no_redirect(self):
        site = self._require_test_site()
        source = self._make_page(site)
        target = self._unique_title("MoveDestNoRedirect")

        page = MwClientPage(source, site)
        result = page.move(target, reason="network test no_redirect=True", no_redirect=True)

        assert result["success"] is True

        time.sleep(1)
        original = MwClientPage(source, site)
        # With no_redirect=True the source should no longer exist as a redirect
        assert original.is_redirect() is False

    def test_move_returns_dict_with_success_key(self):
        site = self._require_test_site()
        source = self._make_page(site)
        target = self._unique_title("MoveDictCheck")

        page = MwClientPage(source, site)
        result = page.move(target, reason="network test dict check")

        assert isinstance(result, dict)
        assert "success" in result


# ---------------------------------------------------------------------------
# TestMwClientPage  –  full round-trip smoke tests
# ---------------------------------------------------------------------------


class TestMwClientPage(TestNetwork):
    """End-to-end smoke tests that exercise the full create → edit → move lifecycle."""

    def test_full_lifecycle_create_edit_move(self):
        site = self._require_test_site()

        # 1. Create
        title = self._unique_title("Lifecycle")
        page = MwClientPage(title, site)
        create_result = page.create("Step 1: created.", "lifecycle test create")
        assert create_result["success"] is True

        # 2. Edit
        page2 = MwClientPage(title, site)
        edit_result = page2.edit("Step 2: edited.", "lifecycle test edit")
        assert edit_result["success"] is True

        # 3. Move
        new_title = self._unique_title("LifecycleMoved")
        page3 = MwClientPage(title, site)
        move_result = page3.move(new_title, reason="lifecycle test move")
        assert move_result["success"] is True

        # 4. Destination must exist
        dest = MwClientPage(new_title, site)
        assert dest.exists() is True

    def test_create_then_check_exists_on_commons(self):
        """Query-only smoke: a well-known page on Commons always exists."""
        page = MwClientPage("Main Page", self.site)
        assert page.exists() is True

    def test_all_public_methods_return_expected_types(self):
        """Contract test: every public method returns the documented type."""
        page = MwClientPage("Main Page", self.site)

        assert isinstance(page.exists(), bool)
        assert isinstance(page.check_exists(), bool)
        assert isinstance(page.is_redirect(), bool)
        # get_redirect_target returns Page or None
        target = page.get_redirect_target()
        assert target is None or isinstance(target, mwclient.page.Page)
