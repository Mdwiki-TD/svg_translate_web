"""
Unit tests for src/main_app/extensions.py module.

Classes to test: BaseModel
"""

from __future__ import annotations

from datetime import datetime

from flask.app import Flask
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.main_app.extensions import db


class MockModel(db.Model):
    __tablename__ = "mock_model"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())


def test_base_model_to_dict(app: Flask) -> None:
    with app.app_context():
        now = datetime(2025, 1, 1, 12, 0, 0)
        obj = MockModel(id=1, name="test", created_at=now)

        data = obj.to_dict()
        assert data["id"] == 1
        assert data["name"] == "test"
        assert data["created_at"] == "2025-01-01T12:00:00"
