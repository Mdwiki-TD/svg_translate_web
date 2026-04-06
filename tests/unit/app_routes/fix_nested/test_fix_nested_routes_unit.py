"""Tests for the fix_nested routes blueprint."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.main_app.app_routes.fix_nested import routes


def test_get_commons_file_url_basic() -> None:
    """Test Commons URL generation for a simple filename."""
    url = routes._get_commons_file_url("Example.svg")
    assert url == "https://commons.wikimedia.org/wiki/File:Example.svg"


def test_get_commons_file_url_with_spaces() -> None:
    """Test Commons URL generation replaces spaces with underscores."""
    url = routes._get_commons_file_url("Example File Name.svg")
    assert url == "https://commons.wikimedia.org/wiki/File:Example_File_Name.svg"


def test_get_commons_file_url_with_special_chars() -> None:
    """Test Commons URL generation encodes special characters."""
    url = routes._get_commons_file_url("Test (2024).svg")
    # Parentheses should be percent-encoded
    assert "File:Test_%282024%29.svg" in url


def test_oauth_required_with_filename_preservation_allows_authenticated(app_mock):
    """Test oauth_required_with_filename_preservation allows authenticated users."""

    @routes.oauth_required_with_filename_preservation
    def protected():
        return "success"

    with app_mock.test_request_context("/fix_nested", method="POST", data={"filename": "Test.svg"}):
        with patch("src.main_app.app_routes.fix_nested.routes.current_user", return_value=MagicMock(username="test")):
            result = protected()
            assert result == "success"


def test_fix_nested_route_registers():
    """Test fix_nested routes are registered."""
    mock_bp = MagicMock()
    routes.bp_fix_nested  # Just ensure the blueprint is importable
    assert routes.bp_fix_nested.name == "fix_nested"
    assert routes.bp_fix_nested.url_prefix == "/fix_nested"
