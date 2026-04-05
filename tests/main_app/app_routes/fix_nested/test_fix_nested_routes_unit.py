"""Tests for the fix_nested routes blueprint."""

from __future__ import annotations

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
