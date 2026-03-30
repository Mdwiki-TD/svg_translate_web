"""
Tests for MwClientPage.
src/main_app/api_services/mwclient_page.py
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
import mwclient.errors

from src.main_app.api_services.mwclient_page import MwClientPage


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
# edit_page
# ══════════════════════════════════════════════════════════════════════════════


class TestEditPageInternal:
    def test_protected_page_error(self, mw_client, mock_page):
        mock_page.edit.side_effect = make_protected_page_error()
        result = mw_client._edit_page(mock_page, "text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert "details" in result


class TestEditPage:

    def test_protected_page_no_retry(self, mw_client, mock_site, mock_page):
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.side_effect = make_protected_page_error()
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        mock_page.edit.assert_called_once()  # no retry on ProtectedPageError

    @patch("src.main_app.api_services.mwclient_page.time.sleep")
    def test_ratelimited_then_protected(self, mock_sleep, mw_client, mock_site, mock_page):
        """Non-ratelimited error during retry should be returned immediately."""
        mock_site.pages.__getitem__.return_value = mock_page
        mock_page.edit.side_effect = [
            make_api_error("ratelimited"),
            make_protected_page_error(),
        ]
        result = mw_client.edit_page("text", "summary")
        assert result["success"] is False
        assert result["error"] == "protectedpageerror"
        assert mock_page.edit.call_count == 2
