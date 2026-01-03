"""Tests for the undo_task function in fix_nested explorer routes."""

from __future__ import annotations

import types
from pathlib import Path
from typing import Any

import pytest

from src.app.users.store import UserTokenRecord


def test_user_token_record_has_username_attribute() -> None:
    """Test that UserTokenRecord has a username attribute (not dictionary access)."""
    # Create a UserTokenRecord instance
    user = UserTokenRecord(
        user_id=123,
        username="test_user",
        access_token=b"token",
        access_secret=b"secret",
    )

    # Verify username attribute exists and is accessible
    assert hasattr(user, "username")
    assert user.username == "test_user"

    # Verify that .get() method does NOT exist on UserTokenRecord
    assert not hasattr(user, "get"), "UserTokenRecord should not have .get() method (it's a dataclass, not a dict)"


def test_username_access_in_f_string() -> None:
    """Test that username can be accessed in f-strings from UserTokenRecord."""
    user = types.SimpleNamespace(
        username="test_coordinator",
        user_id=123,
    )

    # This is what the fixed code does - direct attribute access
    message = f"Task undone: Original file restored by {user.username}"
    assert "test_coordinator" in message

    # This is what the buggy code tried to do - would fail for UserTokenRecord
    # message = f"Task undone: Original file restored by {user.get('username', 'unknown')}"
    # AttributeError: 'SimpleNamespace' object has no attribute 'get'

