"""
Unit tests for extensions module.
"""

from __future__ import annotations

from datetime import datetime

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from src.main_app.extensions import Model, db, migrate


class MockModel(Model):
    __tablename__ = "mock_model"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())


def test_base_model_to_json(mock_app: Flask) -> None:
    # with mock_app.app_context():
    now = datetime(2025, 1, 1, 12, 0, 0)
    obj = MockModel(id=1, name="test", created_at=now)

    data = obj.to_json()
    assert data["id"] == 1
    assert data["name"] == "test"
    assert data["created_at"] == "2025-01-01T12:00:00"


def test_base_model_to_json_isoformat():
    """Test that datetime values are converted to ISO format in to_json."""
    model = MockModel(
        created_at=datetime(2025, 10, 27, 4, 41, 7),
    )

    result = model.to_json()

    assert result["created_at"] == "2025-10-27T04:41:07"


def test_db_is_sqlalchemy_instance():
    """Test that db is a SQLAlchemy instance."""
    assert isinstance(db, SQLAlchemy)


def test_db_session_options():
    """Test that session_options includes expire_on_commit=False in the session factory kwargs."""
    sf_kw = db.session.session_factory.kw
    assert sf_kw.get("expire_on_commit") is False


def test_migrate_is_migrate_instance():
    """Test that migrate is a Migrate instance."""
    assert isinstance(migrate, Migrate)
