"""
Tests for MwClientPage.
src/main_app/api_services/mwclient_page.py
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import mwclient.errors
import pytest


def make_api_error(code: str, info: str = "") -> mwclient.errors.APIError:
    return mwclient.errors.APIError(code, info, {})


@pytest.fixture
def mock_protected_page(code="protectedpage", info="Protected"):
    page = MagicMock()
    return mwclient.errors.ProtectedPageError(page, code, info)


class TestEditPageErrors:

    def test_edit_error(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = mwclient.errors.EditError(mock_exists_page, "edit failed")
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "editerror"
        assert "details" in result

    def test_api_error_other(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = make_api_error("badtoken", "Invalid token")
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "badtoken"
        assert "details" in result

    def test_generic_exception(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = Exception("unexpected crash")
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "unexpected crash"

    def test_unexpected_exception(self, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = RuntimeError("unexpected")
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "unexpected"


class TestEditPageProtectedErrors:

    def test_protected_page_error(self, mock_protected_page, mw_client, mock_exists_page):
        mock_exists_page.edit.side_effect = mock_protected_page
        result = mw_client._edit_page(mock_exists_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert "details" in result

    def test_protected_page_no_retry(self, mock_protected_page, mw_client, mock_site, mock_exists_page):
        mock_site.pages.__getitem__.return_value = mock_exists_page
        mock_exists_page.edit.side_effect = mock_protected_page
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        mock_exists_page.edit.assert_called_once()  # no retry on ProtectedPageError

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_then_protected(self, mock_sleep, mock_protected_page, mw_client, mock_site, mock_exists_page):
        """Non-ratelimited error during retry should be returned immediately."""
        mock_site.pages.__getitem__.return_value = mock_exists_page
        mock_exists_page.edit.side_effect = [
            make_api_error("ratelimited"),
            mock_protected_page,
        ]
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert mock_exists_page.edit.call_count == 2
