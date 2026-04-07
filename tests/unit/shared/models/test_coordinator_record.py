from __future__ import annotations

import pytest
from src.main_app.shared.models.coordinator_record import CoordinatorRecord


def test_coordinator_record_initialization():
    """Test CoordinatorRecord initialization with required fields."""
    rec = CoordinatorRecord(id=1, username="testuser", is_active=True)

    assert rec.id == 1
    assert rec.username == "testuser"
    assert rec.is_active is True
    assert rec.created_at is None
    assert rec.updated_at is None


def test_coordinator_record_with_all_fields():
    """Test CoordinatorRecord initialization with all fields."""
    rec = CoordinatorRecord(id=1, username="testuser", is_active=True, created_at="2023-01-01", updated_at="2023-01-02")

    assert rec.id == 1
    assert rec.username == "testuser"
    assert rec.is_active is True
    assert rec.created_at == "2023-01-01"
    assert rec.updated_at == "2023-01-02"


def test_coordinator_record_inactive():
    """Test CoordinatorRecord with inactive user."""
    rec = CoordinatorRecord(id=1, username="testuser", is_active=False)

    assert rec.id == 1
    assert rec.username == "testuser"
    assert rec.is_active is False
    assert rec.created_at is None
    assert rec.updated_at is None


def test_coordinator_record_to_dict():
    """Test conversion to dictionary."""
    rec = CoordinatorRecord(id=1, username="testuser", is_active=True, created_at="2023-01-01", updated_at="2023-01-02")

    result = rec.to_dict()

    expected = {
        "id": 1,
        "username": "testuser",
        "is_active": True,
        "created_at": "2023-01-01",
        "updated_at": "2023-01-02",
    }

    assert result == expected


def test_coordinator_record_to_dict_with_none_values():
    """Test conversion to dictionary with None values."""
    rec = CoordinatorRecord(id=1, username="testuser", is_active=True, created_at=None, updated_at=None)

    result = rec.to_dict()

    expected = {"id": 1, "username": "testuser", "is_active": True, "created_at": None, "updated_at": None}

    assert result == expected
