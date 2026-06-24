"""
Unit tests for src/main_app/extensions.py module.

Classes to test: BaseModel
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from flask.app import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.main_app.extensions import BaseModel, _commit, db, migrate


class MockModel(db.Model):
    __tablename__ = "mock_model"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


def test_base_model_to_dict(mock_app: Flask) -> None:
    with mock_app.app_context():
        now = datetime(2025, 1, 1, 12, 0, 0)
        obj = MockModel(id=1, name="test", created_at=now)

        data = obj.to_dict()
        assert data["id"] == 1
        assert data["name"] == "test"
        assert data["created_at"] == "2025-01-01T12:00:00"


def test_base_model_to_dict():
    """Test that to_dict serializes column values to a dictionary."""
    model = BaseModel()
    model.foo = "value1"
    model.bar = "value2"

    col1 = MagicMock()
    col1.name = "foo"
    col2 = MagicMock()
    col2.name = "bar"

    table_mock = MagicMock()
    table_mock.columns = [col1, col2]

    with patch.object(BaseModel, "__table__", table_mock, create=True):
        result = model.to_dict()

    assert result == {"foo": "value1", "bar": "value2"}


def test_base_model_to_dict_isoformat():
    """Test that datetime values are converted to ISO format in to_dict."""
    model = BaseModel()
    dt = datetime(2025, 10, 27, 4, 41, 7)
    model.created_at = dt

    col = MagicMock()
    col.name = "created_at"

    table_mock = MagicMock()
    table_mock.columns = [col]

    with patch.object(BaseModel, "__table__", table_mock, create=True):
        result = model.to_dict()

    assert result == {"created_at": "2025-10-27T04:41:07"}


def test_base_model_init_sets_kwargs():
    """Test that __init__ sets provided kwargs as instance attributes when the attribute exists."""
    model = BaseModel()
    model.foo = "original"

    BaseModel.__init__(model, foo="updated", bar="new")

    assert model.foo == "updated"
    assert not hasattr(model, "bar")


def test_base_model_init_skips_nonexistent_attributes():
    """Test that __init__ ignores kwargs for attributes that don't exist on the model."""
    model = BaseModel()

    BaseModel.__init__(model, nonexistent="val")

    assert not hasattr(model, "nonexistent")


def test_commit_calls_commit():
    """Test that _commit calls db.session.commit()."""
    mock_db = MagicMock()
    _commit(mock_db)
    mock_db.session.commit.assert_called_once()


def test_commit_rollback_on_exception():
    """Test that _commit rolls back the session when commit raises."""
    mock_db = MagicMock()
    mock_db.session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError, match="fail"):
        _commit(mock_db)

    mock_db.session.rollback.assert_called_once()


def test_commit_re_raises_exception():
    """Test that _commit re-raises the original exception after rollback."""
    mock_db = MagicMock()
    mock_db.session.commit.side_effect = ValueError("original error")

    with pytest.raises(ValueError, match="original error"):
        _commit(mock_db)

    mock_db.session.rollback.assert_called_once()


def test_db_is_sqlalchemy_instance():
    """Test that db is a SQLAlchemy instance."""
    assert isinstance(db, SQLAlchemy)


def test_db_uses_base_model_class():
    """Test that db.Model inherits from BaseModel, confirming BaseModel was used as model_class."""
    assert issubclass(db.Model, BaseModel)


def test_db_session_options():
    """Test that session_options includes expire_on_commit=False in the session factory kwargs."""
    sf_kw = db.session.session_factory.kw
    assert sf_kw.get("expire_on_commit") is False


def test_migrate_is_migrate_instance():
    """Test that migrate is a Migrate instance."""
    assert isinstance(migrate, Migrate)
