# ruff: noqa: F401
"""
Unit tests for src/main_app/db/exceptions.py module.

Classes to test: DatabaseInitError, MaxUserConnectionsError, UserNotFoundError, DuplicateJobError, InsufficientDatabaseConfigError

TODO: write tests
"""

from __future__ import annotations

import pytest

from src.main_app.db.exceptions import (
    DatabaseInitError,
    DuplicateJobError,
    InsufficientDatabaseConfigError,
    MaxUserConnectionsError,
    UserNotFoundError,
)


def test_max_user_connections_error():
    with pytest.raises(MaxUserConnectionsError):
        raise MaxUserConnectionsError("Too many connections")


def test_insufficient_database_config_error():
    with pytest.raises(InsufficientDatabaseConfigError, match="DB requires database configuration"):
        raise InsufficientDatabaseConfigError()
