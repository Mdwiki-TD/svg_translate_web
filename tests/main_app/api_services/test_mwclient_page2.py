"""
Tests for MwClientPage.
src/main_app/api_services/mwclient_page.py
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, call
import pytest
import mwclient.errors

from src.main_app.api_services.mwclient_page import MwClientPage, _RETRY_DELAYS


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_site():
    return MagicMock()


@pytest.fixture
def mock_page():
    page = MagicMock()
    page.exists = True
    return page


@pytest.fixture
def mw_client(mock_site):
    return MwClientPage("Test Page", mock_site)


# ── helpers ────────────────────────────────────────────────────────────────────

def make_api_error(code: str, info: str = "") -> mwclient.errors.APIError:
    return mwclient.errors.APIError(code, info, {})


def make_protected_page_error(code="protectedpage", info="Protected"):
    page = MagicMock()
    return mwclient.errors.ProtectedPageError(page, code, info)


# ══════════════════════════════════════════════════════════════════════════════
# load_page
# ══════════════════════════════════════════════════════════════════════════════

class TestLoadPage:
    def test_returns_page_on_success(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        result = mw_client.load_page()
        assert result is mock_page

    def test_caches_page_on_second_call(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mw_client.load_page()
        mw_client.load_page()
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


# ══════════════════════════════════════════════════════════════════════════════
# check_exists
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckExists:
    def test_returns_true_when_page_exists(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        assert mw_client.check_exists() is True

    def test_returns_false_when_page_missing(self, mw_client, mock_site, mock_page):
        mock_page.exists = False
        mock_site.pages.__getitem__.return_value = mock_page
        assert mw_client.check_exists() is False

    def test_returns_false_when_load_fails(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle("bad")
        assert mw_client.check_exists() is False


# ══════════════════════════════════════════════════════════════════════════════
# _edit_page
# ══════════════════════════════════════════════════════════════════════════════

class TestEditPageInternal:
    def test_success(self, mw_client, mock_page):
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result == {"success": True}
        mock_page.edit.assert_called_once_with("text", summary="summary")

    def test_edit_error(self, mw_client, mock_page):
        mock_page.edit.side_effect = mwclient.errors.EditError(mock_page, "edit failed")
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "editerror"
        assert "details" in result

    def test_assert_user_failed(self, mw_client, mock_page):
        mock_page.edit.side_effect = mwclient.errors.AssertUserFailedError()
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result == {"success": False, "error": "assertuserfailed"}

    def test_user_blocked(self, mw_client, mock_page):
        mock_page.edit.side_effect = mwclient.errors.UserBlocked(MagicMock())
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result == {"success": False, "error": "userblocked"}

    def test_protected_page_error(self, mw_client, mock_page):
        mock_page.edit.side_effect = make_protected_page_error()
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert "details" in result

    def test_rate_limited(self, mw_client, mock_page):
        mock_page.edit.side_effect = make_api_error("ratelimited")
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result == {"success": False, "error": "ratelimited"}

    def test_other_api_error(self, mw_client, mock_page):
        mock_page.edit.side_effect = make_api_error("badtoken", "Invalid token")
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "badtoken"
        assert "details" in result

    def test_generic_exception(self, mw_client, mock_page):
        mock_page.edit.side_effect = Exception("unexpected crash")
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "unexpected crash"


# ══════════════════════════════════════════════════════════════════════════════
# edit_page
# ══════════════════════════════════════════════════════════════════════════════

class TestEditPage:
    def test_success(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        result = mw_client.edit_page("text", "summary")
        assert result == {"success": True}

    def test_load_page_fails_invalid_title(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle("bad")
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "invalidpagetitle"

    def test_load_page_fails_generic(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = Exception("network error")
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "network error"

    def test_rate_limited_then_success(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.side_effect = [
            make_api_error("ratelimited"),
            None,  # second attempt succeeds
        ]
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_page("text", "summary")
        assert result == {"success": True}

    def test_rate_limited_exhausts_all_retries(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.side_effect = make_api_error("ratelimited")
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_page("text", "summary")
        assert result == {"success": False, "error": "ratelimited"}
        # 1 initial attempt + len(_RETRY_DELAYS) retries
        assert mock_page.edit.call_count == 1 + len(_RETRY_DELAYS)

    def test_rate_limited_sleeps_correct_delays(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.side_effect = make_api_error("ratelimited")
        with patch("src.main_app.api_services.mwclient_page.time.sleep") as mock_sleep:
            mw_client.edit_page("text", "summary")
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == list(_RETRY_DELAYS)

    def test_rate_limited_then_protected(self, mw_client, mock_site, mock_page):
        """Non-ratelimited error during retry should be returned immediately."""
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.side_effect = [
            make_api_error("ratelimited"),
            make_protected_page_error(),
        ]
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert mock_page.edit.call_count == 2


# ══════════════════════════════════════════════════════════════════════════════
# edit_with_retry (direct)
# ══════════════════════════════════════════════════════════════════════════════

class TestEditWithRetry:
    def test_succeeds_on_first_retry(self, mw_client, mock_page):
        mock_page.edit.side_effect = [None]  # succeeds immediately
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_with_retry(mock_page, "text", "summary")
        assert result == {"success": True}

    def test_returns_ratelimited_after_all_retries(self, mw_client, mock_page):
        mock_page.edit.side_effect = make_api_error("ratelimited")
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_with_retry(mock_page, "text", "summary")
        assert result == {"success": False, "error": "ratelimited"}
        assert mock_page.edit.call_count == len(_RETRY_DELAYS)

    def test_stops_early_on_non_ratelimited_error(self, mw_client, mock_page):
        mock_page.edit.side_effect = [
            make_api_error("ratelimited"),
            mwclient.errors.AssertUserFailedError(),
        ]
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_with_retry(mock_page, "text", "summary")
        assert result == {"success": False, "error": "assertuserfailed"}
        assert mock_page.edit.call_count == 2
