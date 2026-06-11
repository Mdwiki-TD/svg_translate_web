"""
Unit tests for src/main_app/api_services/mwclient_page/mwclient_error.py
"""

from __future__ import annotations

from unittest.mock import MagicMock

import mwclient.errors
from mwclient.client import Site

from src.main_app.api_services.mwclient_page.mwclient_error import handle_mwclient_error

# ---------------------------------------------------------------------------
# handle_mwclient_error
# ---------------------------------------------------------------------------


class TestHandleApiError:
    """Unit tests for the module-level handle_mwclient_error helper."""

    def test_protected_page_error(self):
        exc = mwclient.errors.ProtectedPageError(MagicMock(), "protectedpage", "Protected")
        result = handle_mwclient_error(exc)
        assert result is not None
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert "details" in result

    def test_edit_error(self):
        exc = mwclient.errors.EditError(MagicMock(), "edit-conflict", "Edit conflict")
        result = handle_mwclient_error(exc)
        assert result is not None
        assert result["success"] is False
        assert result["error"] == "editerror"

    def test_assert_user_failed(self):
        exc = mwclient.errors.AssertUserFailedError()
        result = handle_mwclient_error(exc)
        assert result == {"success": False, "error": "assertuserfailed"}

    def test_user_blocked(self):
        exc = mwclient.errors.UserBlocked(MagicMock(), "blocked", "Blocked")
        result = handle_mwclient_error(exc)
        assert result == {"success": False, "error": "userblocked"}

    def test_api_error_ratelimited(self):
        exc = mwclient.errors.APIError("ratelimited", "Rate limited", "")
        result = handle_mwclient_error(exc)
        assert result == {"success": False, "error": "ratelimited"}

    def test_api_error_other_code(self):
        exc = mwclient.errors.APIError("badtoken", "Invalid token", "")
        result = handle_mwclient_error(exc)
        assert result is not None
        assert result["success"] is False
        assert result["error"] == "badtoken"

    def test_unrecognised_exception_returns_none(self):
        exc = ValueError("something unexpected")
        result = handle_mwclient_error(exc)
        assert result is None

    def test_runtime_error_returns_none(self):
        result = handle_mwclient_error(RuntimeError("boom"))
        assert result is None
