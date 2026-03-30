"""
Tests for MwClientPage.
src/main_app/api_services/mwclient_page.py
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, call
import pytest
import mwclient.errors

from src.main_app.api_services.mwclient_page import MwClientPage

# ── fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_site():
    site = MagicMock()
    return site


@pytest.fixture
def mock_page():
    page = MagicMock()
    page.exists = True
    return page


@pytest.fixture
def mw_client(mock_site):
    return MwClientPage("Test Page", mock_site)


# ── load_page ──────────────────────────────────────────────────────────────────

class TestLoadPage:
    def test_returns_page_on_success(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        result = mw_client.load_page()
        assert result == mock_page

    def test_caches_page_on_second_call(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mw_client.load_page()
        mw_client.load_page()
        # site.pages should only be accessed once
        mock_site.pages.__getitem__.assert_called_once()

    def test_invalid_page_title(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle("bad title")
        result = mw_client.load_page()
        assert result is False
        assert mw_client.load_page_error == "invalidpagetitle"

    def test_generic_exception(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = Exception("connection error")
        result = mw_client.load_page()
        assert result is False
        assert mw_client.load_page_error == "connection error"


# ── check_exists ───────────────────────────────────────────────────────────────

class TestCheckExists:
    def test_page_exists(self, mw_client, mock_site, mock_page):
        mock_page.exists = True
        mock_site.pages.__getitem__.return_value = mock_page
        assert mw_client.check_exists() is True

    def test_page_does_not_exist(self, mw_client, mock_site, mock_page):
        mock_page.exists = False
        mock_site.pages.__getitem__.return_value = mock_page
        assert mw_client.check_exists() is False

    def test_load_page_fails(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle("x")
        assert mw_client.check_exists() is False


# ── _edit_page ─────────────────────────────────────────────────────────────────

class TestEditPageInternal:
    def test_success(self, mw_client, mock_page):
        mock_page.edit.return_value = None
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result == {"success": True}

    def test_edit_error(self, mw_client, mock_page):
        mock_page.edit.side_effect = mwclient.errors.EditError(mock_page, {})
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "editerror"
        assert "details" in result

    def test_protected_page_error(self, mw_client, mock_page):
        exc = mwclient.errors.ProtectedPageError(mock_page, "protectedpage", "Page is protected")
        mock_page.edit.side_effect = exc
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert "details" in result

    def test_ratelimited(self, mw_client, mock_page):
        exc = mwclient.errors.APIError("ratelimited", "Rate limited", {})
        mock_page.edit.side_effect = exc
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result == {"success": False, "error": "ratelimited"}

    def test_api_error_other(self, mw_client, mock_page):
        exc = mwclient.errors.APIError("badtoken", "Bad token", {})
        mock_page.edit.side_effect = exc
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "badtoken"
        assert "details" in result

    def test_unexpected_exception(self, mw_client, mock_page):
        mock_page.edit.side_effect = RuntimeError("unexpected")
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "unexpected"


# ── edit_page ──────────────────────────────────────────────────────────────────

class TestEditPage:
    def test_success(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.return_value = None
        result = mw_client.edit_page("text", "summary")
        assert result == {"success": True}

    def test_load_page_fails_invalid_title(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle("x")
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "invalidpagetitle"

    def test_load_page_fails_generic(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = Exception("network error")
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "network error"

    def test_edit_error_no_retry(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.side_effect = mwclient.errors.EditError(mock_page, {})
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "editerror"
        mock_page.edit.assert_called_once()  # no retry on EditError

    def test_protected_page_no_retry(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        exc = mwclient.errors.ProtectedPageError(mock_page, "protectedpage", "Protected")
        mock_page.edit.side_effect = exc
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        mock_page.edit.assert_called_once()  # no retry on ProtectedPageError

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_then_success(self, mock_sleep, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        rate_exc = mwclient.errors.APIError("ratelimited", "Rate limited", {})
        # fail once, then succeed
        mock_page.edit.side_effect = [rate_exc, None]
        result = mw_client.edit_page("text", "summary")
        assert result == {"success": True}
        mock_sleep.assert_called_once_with(5)  # first delay only

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_exhausts_all_retries(self, mock_sleep, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        rate_exc = mwclient.errors.APIError("ratelimited", "Rate limited", {})
        # always rate limited: 1 initial + 3 retries = 4 calls total
        mock_page.edit.side_effect = rate_exc
        result = mw_client.edit_page("text", "summary")
        assert result == {"success": False, "error": "ratelimited"}
        assert mock_page.edit.call_count == 4
        assert mock_sleep.call_count == 3
        mock_sleep.assert_has_calls([call(5), call(15), call(30)])

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_then_other_api_error(self, mock_sleep, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        rate_exc = mwclient.errors.APIError("ratelimited", "Rate limited", {})
        other_exc = mwclient.errors.APIError("badtoken", "Bad token", {})
        # rate limited first, then a different API error
        mock_page.edit.side_effect = [rate_exc, other_exc]
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "badtoken"
        mock_sleep.assert_called_once_with(5)

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_retry_sleep_delays_are_correct(self, mock_sleep, mw_client, mock_site, mock_page):
        """Verify the exact delay sequence: 5s, 15s, 30s."""
        mock_site.pages.__getitem__.return_value = mock_page
        rate_exc = mwclient.errors.APIError("ratelimited", "Rate limited", {})
        mock_page.edit.side_effect = rate_exc
        mw_client.edit_page("text", "summary")
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [5, 15, 30]
