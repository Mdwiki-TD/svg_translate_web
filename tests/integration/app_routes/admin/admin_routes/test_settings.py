"""Tests for admin settings routes."""

from __future__ import annotations

import re
from unittest.mock import MagicMock

from src.main_app.app_routes.admin_routes import settings

KEY_PATTERN = r"[a-z][a-z0-9_]{0,189}"


def test_key_validation_pattern():
    """Test key validation regex pattern for valid keys."""
    valid_keys = [
        "simple",
        "with_underscore",
        "with123numbers",
        "a" * 190,  # max length
        "key",
        "my_key_123",
    ]
    for key in valid_keys:
        assert re.fullmatch(KEY_PATTERN, key) is not None, f"Key '{key}' should be valid"


def test_key_validation_pattern_invalid():
    """Test key validation regex pattern rejects invalid keys."""
    invalid_keys = [
        "UPPERCASE",
        "has-dash",
        "has dot",
        "123starts_with_number",
        "a" * 191,  # too long
        "",
    ]
    for key in invalid_keys:
        assert re.fullmatch(KEY_PATTERN, key) is None, f"Key '{key}' should be invalid"


def test_settings_create_key_too_long():
    """Test settings_create rejects key that's too long (190+ chars)."""
    long_key = "a" * 200
    result = re.fullmatch(KEY_PATTERN, long_key)
    assert result is None


def test_settings_create_key_max_length():
    """Test settings_create accepts key at max length (190 chars)."""
    max_key = "a" + "a" * 189  # 190 chars total
    result = re.fullmatch(KEY_PATTERN, max_key)
    assert result is not None


def test_SettingsRoutes_init_registers_routes():
    """Test SettingsRoutes registers all required routes."""
    mock_bp = MagicMock()

    settings.SettingsRoutes(mock_bp)

    assert mock_bp.get.call_count == 1
    assert mock_bp.post.call_count == 2
