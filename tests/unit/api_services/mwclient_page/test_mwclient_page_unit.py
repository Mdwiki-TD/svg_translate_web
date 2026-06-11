"""
Unit tests for src/main_app/api_services/mwclient_page/mwclient_wraper.py

All external I/O is mocked — these tests run instantly with no network access.
Run them with:  pytest tests/unit/  (or simply: pytest)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import mwclient.errors
import pytest
from mwclient.client import Site

from src.main_app.api_services.mwclient_page.mwclient_wraper import MwClientPage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.mwclient_page.mwclient_wraper.time.sleep",
        _mock,
    )
    return _mock


def _make_site() -> MagicMock:
    """Return a minimal mock Site."""
    return MagicMock(name="site")


@pytest.fixture
def mwclient_wrapper(mock_site) -> MwClientPage:
    site = mock_site
    return MwClientPage("T", site)


def _make_page(*, exists: bool = True, is_redirect: bool = False) -> MagicMock:
    """Return a mock mwclient.page.Page."""
    page = MagicMock(name="mw_page")
    page.exists = exists
    page.redirects_to.return_value = MagicMock(name="redirect_target") if is_redirect else None
    return page


def _mwclient_page(exists: bool = True) -> tuple[MwClientPage, MagicMock]:
    """Return (MwClientPage, inner_mock_page) with load_page pre-wired."""
    _site = MagicMock()
    mock_page = _make_page(exists=exists)
    _site.pages.__getitem__ = MagicMock(return_value=mock_page)
    wrapper = MwClientPage("Test Page", _site)
    return wrapper, mock_page


# ---------------------------------------------------------------------------
# MwClientPage.__init__
# ---------------------------------------------------------------------------


class TestInit:
    def test_initial_state(self, mock_site):
        site = mock_site
        wrapper = MwClientPage("Some Title", site)

        assert wrapper.title == "Some Title"
        assert wrapper.site is site
        assert wrapper.page is None
        assert wrapper.load_page_error == ""


# ---------------------------------------------------------------------------
# load_page
# ---------------------------------------------------------------------------


class TestLoadPage:
    def test_returns_page_on_success(self):
        wrapper, mock_page = _mwclient_page()
        result = wrapper.load_page()
        assert result is mock_page

    def test_caches_page_on_second_call(self):
        wrapper, mock_page = _mwclient_page()
        first = wrapper.load_page()
        second = wrapper.load_page()
        # site.pages.__getitem__ must only be called once
        assert first is second
        assert wrapper.site.pages.__getitem__.call_count == 1

    def test_sets_error_on_invalid_title(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle(MagicMock(), "")
        wrapper = MwClientPage("[Bad<Title>]", site)
        result = wrapper.load_page()
        assert result is None
        assert wrapper.load_page_error == "invalidpagetitle"

    def test_sets_error_on_generic_exception(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = ConnectionError("network down")
        wrapper = MwClientPage("Any Title", site)
        result = wrapper.load_page()
        assert result is None
        assert "network down" in wrapper.load_page_error

    def test_returns_none_when_already_failed(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = mwclient.errors.InvalidPageTitle(MagicMock(), "")
        wrapper = MwClientPage("Bad", site)
        wrapper.load_page()  # first call sets the error
        result = wrapper.load_page()  # second call: page is None, should not re-raise
        assert result is None


# ---------------------------------------------------------------------------
# exists / check_exists
# ---------------------------------------------------------------------------


class TestExists:
    def test_true_when_page_exists(self):
        wrapper, _ = _mwclient_page(exists=True)
        assert wrapper.exists() is True

    def test_false_when_page_missing(self):
        wrapper, _ = _mwclient_page(exists=False)
        assert wrapper.exists() is False

    def test_false_when_load_page_fails(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = ConnectionError("offline")
        wrapper = MwClientPage("Any", site)
        assert wrapper.exists() is False

    def test_check_exists_is_alias_for_exists(self):
        wrapper, _ = _mwclient_page(exists=True)
        assert wrapper.check_exists() == wrapper.exists()


# ---------------------------------------------------------------------------
# get_redirect_target
# ---------------------------------------------------------------------------


class TestGetRedirectTarget:
    def test_returns_target_for_redirect_page(self):
        wrapper, mock_page = _mwclient_page()
        target = MagicMock(name="redirect_target")
        target.name = "Redirect Target Title"
        mock_page.redirects_to.return_value = target

        result = wrapper.get_redirect_target()

        assert result == "Redirect Target Title"

    def test_returns_none_for_non_redirect(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.redirects_to.return_value = None

        result = wrapper.get_redirect_target()
        assert result is None

    def test_returns_none_when_redirects_to_raises(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.redirects_to.side_effect = Exception("not a redirect")

        result = wrapper.get_redirect_target()
        assert result is None

    def test_returns_none_when_page_missing(self):
        wrapper, mock_page = _mwclient_page(exists=False)
        result = wrapper.get_redirect_target()
        assert result is None

    def test_returns_none_when_load_fails(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = ConnectionError
        wrapper = MwClientPage("Any", site)
        assert wrapper.get_redirect_target() is None


# ---------------------------------------------------------------------------
# is_redirect
# ---------------------------------------------------------------------------


class TestIsRedirect:
    def test_true_for_redirect_page(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.redirects_to.return_value = MagicMock()
        assert wrapper.is_redirect() is True

    def test_false_for_non_redirect(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.redirects_to.return_value = None
        assert wrapper.is_redirect() is False

    def test_false_when_page_missing(self):
        wrapper, _ = _mwclient_page(exists=False)
        assert wrapper.is_redirect() is False


# ---------------------------------------------------------------------------
# edit / edit_page
# ---------------------------------------------------------------------------


class TestEdit:
    def test_success(self):
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.edit.return_value = {"result": "Success"}

        result = wrapper.edit("content", "summary")

        assert result["success"] is True
        mock_page.edit.assert_called_once_with("content", summary="summary", nocreate=True)

    def test_nocreate_passed_through(self):
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.edit.return_value = {}

        wrapper.edit("content", "summary", nocreate=False)

        mock_page.edit.assert_called_once_with("content", summary="summary", nocreate=False)

    def test_returns_failure_when_load_page_fails(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = ConnectionError("down")
        wrapper = MwClientPage("X", site)

        result = wrapper.edit("content", "summary")

        assert result["success"] is False

    def test_protected_page_error_propagates(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.edit.side_effect = mwclient.errors.ProtectedPageError(MagicMock(), "protectedpage", "Protected")
        result = wrapper.edit("content", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"

    def test_assert_user_failed_propagates(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.edit.side_effect = mwclient.errors.AssertUserFailedError()
        result = wrapper.edit("content", "summary")
        assert result == {"success": False, "error": "assertuserfailed"}

    def test_unknown_exception_returns_failure(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.edit.side_effect = RuntimeError("unexpected")
        result = wrapper.edit("content", "summary")
        assert result["success"] is False
        assert "unexpected" in result["error"]

    def test_edit_page_alias(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.edit.return_value = {}
        r1 = wrapper.edit("txt", "sum")
        # reset and call via alias on a fresh wrapper to compare behaviour
        wrapper2, mock_page2 = _mwclient_page()
        mock_page2.edit.return_value = {}
        r2 = wrapper2.edit_page("txt", "sum")
        assert r1["success"] == r2["success"]


# ---------------------------------------------------------------------------
# create / create_page
# ---------------------------------------------------------------------------


class TestCreate:
    def test_success_on_new_page(self):
        wrapper, mock_page = _mwclient_page(exists=False)
        mock_page.edit.return_value = {"result": "Success"}

        result = wrapper.create("content", "summary")

        assert result["success"] is True
        mock_page.edit.assert_called_once_with("content", summary="summary", createonly=True)

    def test_fails_when_page_already_exists(self):
        wrapper, _ = _mwclient_page(exists=True)
        result = wrapper.create("content", "summary")
        assert result == {"success": False, "error": "page exists"}

    def test_fails_when_load_page_fails(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = ConnectionError("down")
        wrapper = MwClientPage("New", site)
        result = wrapper.create("content", "summary")
        assert result["success"] is False

    def test_create_page_alias(self):
        wrapper, mock_page = _mwclient_page(exists=False)
        mock_page.edit.return_value = {}
        result = wrapper.create_page("content", "summary")
        assert result["success"] is True

    def test_edit_error_propagates(self):
        wrapper, mock_page = _mwclient_page(exists=False)
        mock_page.edit.side_effect = mwclient.errors.EditError(MagicMock(), "conflict", "Conflict")
        result = wrapper.create("content", "summary")
        assert result["success"] is False
        assert result["error"] == "editerror"


# ---------------------------------------------------------------------------
# move / move_page
# ---------------------------------------------------------------------------


class TestMove:
    def test_success(self):
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.move.return_value = {"moved": "ok"}

        result = wrapper.move("New Title", reason="reason")

        assert result["success"] is True
        mock_page.move.assert_called_once_with("New Title", reason="reason", move_talk=True, no_redirect=False)

    def test_fails_when_page_missing(self):
        wrapper, _ = _mwclient_page(exists=False)
        result = wrapper.move("New Title")
        assert result == {"success": False, "error": "missing"}

    def test_fails_when_load_page_fails(self, mock_site):
        site = mock_site
        site.pages.__getitem__.side_effect = ConnectionError("down")
        wrapper = MwClientPage("Old", site)
        result = wrapper.move("New")
        assert result["success"] is False

    def test_move_talk_and_no_redirect_forwarded(self):
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.move.return_value = {}

        wrapper.move("T", reason="r", move_talk=False, no_redirect=True)

        mock_page.move.assert_called_once_with("T", reason="r", move_talk=False, no_redirect=True)

    def test_protected_page_error_propagates(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.move.side_effect = mwclient.errors.ProtectedPageError(MagicMock(), "protectedpage", "Protected")
        result = wrapper.move("T")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"

    def test_move_page_alias(self):
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.move.return_value = {}
        result = wrapper.move_page("New Title", reason="r")
        assert result["success"] is True


# ---------------------------------------------------------------------------
# _with_retry  (rate-limit retry logic)
# ---------------------------------------------------------------------------


class TestWithRetry:
    """Tests for the internal _with_retry mechanism."""

    def test_succeeds_immediately_when_no_rate_limit(self, mwclient_wrapper):
        op = MagicMock(return_value={"success": True})

        result = mwclient_wrapper._with_retry(op)

        assert result == {"success": True}
        assert op.call_count == 1

    def test_retries_on_rate_limit_then_succeeds(self, mwclient_wrapper, mock_sleep):
        op = MagicMock(
            side_effect=[
                {"success": False, "error": "ratelimited"},
                {"success": True},
            ]
        )

        result = mwclient_wrapper._with_retry(op)

        assert result["success"] is True
        assert op.call_count == 2
        mock_sleep.assert_called_once()  # one sleep between the two attempts

    def test_exhausts_all_retries_and_returns_ratelimited(self, mwclient_wrapper, mock_sleep):
        # Always rate-limited — first call + 3 retries = 4 total calls
        op = MagicMock(return_value={"success": False, "error": "ratelimited"})

        result = mwclient_wrapper._with_retry(op)

        assert result == {"success": False, "error": "ratelimited"}
        assert op.call_count == 4  # 1 initial + 3 retries
        assert mock_sleep.call_count == 3  # sleep before each retry

    def test_sleep_durations_match_retry_delays(self, mwclient_wrapper, mock_sleep):
        op = MagicMock(return_value={"success": False, "error": "ratelimited"})

        mwclient_wrapper._with_retry(op)

        sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
        assert sleep_args == [5, 15, 30]

    def test_stops_retrying_once_non_ratelimit_error_received(self, mwclient_wrapper, mock_sleep):
        op = MagicMock(
            side_effect=[
                {"success": False, "error": "ratelimited"},
                {"success": False, "error": "protectedpageerror"},
            ]
        )

        result = mwclient_wrapper._with_retry(op)

        assert result["error"] == "protectedpageerror"
        assert op.call_count == 2
        mock_sleep.assert_called_once()

    def test_edit_retries_on_rate_limit(self, mock_sleep):
        """Full integration of edit() + _with_retry."""
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.edit.side_effect = [
            mwclient.errors.APIError("ratelimited", "Rate limited", ""),
            {"result": "Success"},
        ]

        result = wrapper.edit("content", "summary")

        assert result["success"] is True
        assert mock_page.edit.call_count == 2
        mock_sleep.assert_called_once_with(5)

    def test_move_retries_on_rate_limit(self):
        """Full integration of move() + _with_retry."""
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.move.side_effect = [
            mwclient.errors.APIError("ratelimited", "Rate limited", ""),
            {"moved": "ok"},
        ]

        result = wrapper.move("New Title")

        assert result["success"] is True
        assert mock_page.move.call_count == 2


# ---------------------------------------------------------------------------
# _edit_page (internal helper — tested via edit/create public API)
# ---------------------------------------------------------------------------


class TestEditPageInternal:
    """Edge-case tests for _edit_page that are easier to reach directly."""

    def test_none_return_from_page_edit_treated_as_success(self):
        """mwclient.Page.edit() can return None; the wrapper should still succeed."""
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.edit.return_value = None  # some mwclient versions do this

        result = wrapper.edit("content", "summary")

        assert result["success"] is True

    def test_user_blocked_returns_failure(self):
        wrapper, mock_page = _mwclient_page()
        mock_page.edit.side_effect = mwclient.errors.UserBlocked(MagicMock(), "blocked", "You are blocked")
        result = wrapper.edit("content", "summary")
        assert result == {"success": False, "error": "userblocked"}


# ---------------------------------------------------------------------------
# _move_page (internal helper — tested via move public API)
# ---------------------------------------------------------------------------


class TestMovePageInternal:
    def test_none_return_from_page_move_treated_as_success(self):
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.move.return_value = None

        result = wrapper.move("New Title")

        assert result["success"] is True

    def test_unknown_exception_returns_failure(self):
        wrapper, mock_page = _mwclient_page(exists=True)
        mock_page.move.side_effect = RuntimeError("unexpected move error")
        result = wrapper.move("New Title")
        assert result["success"] is False
        assert "unexpected move error" in result["error"]
