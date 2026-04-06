"""Unit tests for the Flask application factory helpers."""

from __future__ import annotations

def test_format_stage_timestamp_valid():
    """Test format_stage_timestamp with valid timestamp."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T04:41:07")

    assert "Oct 27, 2025" in result
    assert "4:41 AM" in result


def test_format_stage_timestamp_empty():
    """Test format_stage_timestamp with empty string."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("")

    assert result == ""


def test_format_stage_timestamp_invalid():
    """Test format_stage_timestamp with invalid timestamp."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("invalid-timestamp")

    assert result == ""


def test_format_stage_timestamp_afternoon():
    """Test format_stage_timestamp with PM time."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T16:41:07")

    assert "Oct 27, 2025" in result
    assert "4:41 PM" in result


def test_format_stage_timestamp_noon():
    """Test format_stage_timestamp with noon."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T12:00:00")

    assert "Oct 27, 2025" in result
    assert "12:00 PM" in result


def test_format_stage_timestamp_midnight():
    """Test format_stage_timestamp with midnight."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T00:00:00")

    assert "Oct 27, 2025" in result
    assert "12:00 AM" in result
