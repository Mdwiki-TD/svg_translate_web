"""
Tests for MwClientPage.
src/main_app/api_services/mwclient_page.py
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, call
import mwclient.errors

from src.main_app.api_services.mwclient_page import _RETRY_DELAYS


def make_api_error(code: str, info: str = "") -> mwclient.errors.APIError:
    return mwclient.errors.APIError(code, info, {})

# ══════════════════════════════════════════════════════════════════════════════
# load_page
# ══════════════════════════════════════════════════════════════════════════════


class TestLoadPage:
    def test_returns_page_on_success(self, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
        result = mw_client.load_page()
        assert result == mock_exists_page

    def test_caches_page_on_second_call(self, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
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


# ══════════════════════════════════════════════════════════════════════════════
# check_exists
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckExists:
    def test_page_exists(self, mw_client, mock_site, mock_exists_page):
        mock_exists_page.exists = True
        mock_site.pages.__getitem__.return_value = mock_exists_page
        assert mw_client.check_exists() is True

    def test_page_does_not_exist(self, mw_client, mock_site, mock_exists_page):
        mock_exists_page.exists = False
        mock_site.pages.__getitem__.return_value = mock_exists_page
        assert mw_client.check_exists() is False

    def test_load_page_fails(self, mw_client, mock_site):
        mock_site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle("bad")
        assert mw_client.check_exists() is False


# ══════════════════════════════════════════════════════════════════════════════
# _edit_page
# ══════════════════════════════════════════════════════════════════════════════

class TestEditPageInternal:

    def test_success(self, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
        mock_exists_page.edit.return_value = None
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        mock_exists_page.edit.assert_called_once_with("text", summary="summary")
        assert result == {"success": True}

    def test_assert_user_failed(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = mwclient.errors.AssertUserFailedError()
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result == {"success": False, "error": "assertuserfailed"}

    def test_user_blocked(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = mwclient.errors.UserBlocked(MagicMock())
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result == {"success": False, "error": "userblocked"}


# ══════════════════════════════════════════════════════════════════════════════
# edit_page
# ══════════════════════════════════════════════════════════════════════════════

class TestEditPage:
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


class TestEditPageRateLimit:
    def test_ratelimited(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = make_api_error("ratelimited", "Rate limited")
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result == {"success": False, "error": "ratelimited"}

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_then_success(self, mock_sleep, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
        rate_exc = make_api_error("ratelimited", "Rate limited")
        # fail once, then succeed
        mock_exists_page.edit.side_effect = [
            rate_exc,
            None,  # second attempt succeeds
        ]
        result = mw_client.edit_page("text", "summary")
        assert result == {"success": True}
        mock_sleep.assert_called_once_with(5)  # first delay only

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_exhausts_all_retries(self, mock_sleep, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
        rate_exc = make_api_error("ratelimited", "Rate limited")
        # always rate limited: 1 initial + 3 retries = 4 calls total
        mock_exists_page.edit.side_effect = rate_exc
        result = mw_client.edit_page("text", "summary")
        assert result == {"success": False, "error": "ratelimited"}
        # 1 initial attempt + len(_RETRY_DELAYS) retries
        assert mock_exists_page.edit.call_count == 1 + len(_RETRY_DELAYS)

        assert mock_exists_page.edit.call_count == 4
        assert mock_sleep.call_count == 3
        mock_sleep.assert_has_calls([call(5), call(15), call(30)])

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_then_other_api_error(self, mock_sleep, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
        rate_exc = make_api_error("ratelimited", "Rate limited")
        other_exc = make_api_error("badtoken", "Bad token")
        # rate limited first, then a different API error
        mock_exists_page.edit.side_effect = [rate_exc, other_exc]
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "badtoken"
        mock_sleep.assert_called_once_with(5)

    def test_edit_error_no_retry(self, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
        mock_exists_page.edit.side_effect = mwclient.errors.EditError(mock_exists_page, {})
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "editerror"
        mock_exists_page.edit.assert_called_once()  # no retry on EditError

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_retry_sleep_delays_are_correct(self, mock_sleep, mw_client, mock_site, mock_exists_page):
        """Verify the exact delay sequence: 5s, 15s, 30s."""
        mock_site.pages.__getitem__.return_value = mock_exists_page
        rate_exc = make_api_error("ratelimited", "Rate limited")
        mock_exists_page.edit.side_effect = rate_exc
        mw_client.edit_page("text", "summary")
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == list(_RETRY_DELAYS)

# ══════════════════════════════════════════════════════════════════════════════
# edit_with_retry (direct)
# ══════════════════════════════════════════════════════════════════════════════


class TestEditWithRetry:
    def test_succeeds_on_first_retry(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = [None]  # succeeds immediately
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_with_retry(mock_exists_page, "text", "summary")
        assert result == {"success": True}

    def test_returns_ratelimited_after_all_retries(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = make_api_error("ratelimited")
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_with_retry(mock_exists_page, "text", "summary")
        assert result == {"success": False, "error": "ratelimited"}
        assert mock_exists_page.edit.call_count == len(_RETRY_DELAYS)

    def test_stops_early_on_non_ratelimited_error(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = [
            make_api_error("ratelimited"),
            mwclient.errors.AssertUserFailedError(),
        ]
        with patch("src.main_app.api_services.mwclient_page.time.sleep"):
            result = mw_client.edit_with_retry(mock_exists_page, "text", "summary")
        assert result == {"success": False, "error": "assertuserfailed"}
        assert mock_exists_page.edit.call_count == 2
