"""
Unit tests for src/main_app/db/models/users.py module.

Classes to test: UserRecord, AdminUserRecord, UserTokenRecord
"""

from __future__ import annotations

from flask.app import Flask

from src.main_app.core.crypto import encrypt_value
from src.main_app.db.models.users import (
    AdminUserRecord,
    UserRecord,
    UserTokenRecord,
)
from src.main_app.extensions import db


def test_users_record(mock_app: Flask) -> None:
    with mock_app.app_context():
        user = UserRecord(user_id=42, username="model_test_user")
        db.session.add(user)
        db.session.commit()

        assert user.user_id == 42
        assert user.username == "model_test_user"
        assert user.created_at is not None


def test_admin_user_record(mock_app: Flask) -> None:
    with mock_app.app_context():
        user = UserRecord(user_id=1, username="model_admin_user")
        db.session.add(user)
        db.session.commit()

        admin = AdminUserRecord(username="model_admin_user", is_active=True)
        db.session.add(admin)
        db.session.commit()

        assert admin.id is not None
        assert admin.username == "model_admin_user"
        assert admin.is_active is True


def test_user_token_record(mock_app: Flask) -> None:
    with mock_app.app_context():
        user = UserRecord(user_id=123, username="model_token_user")
        db.session.add(user)
        db.session.commit()

        token = encrypt_value("access_token_val")
        secret = encrypt_value("access_secret_val")

        user_token = UserTokenRecord(user_id=123, access_token=token, access_secret=secret)
        db.session.add(user_token)
        db.session.commit()

        assert user_token.user_id == 123
        assert user_token.user.username == "model_token_user"

        assert user_token.access_token != b"access_token_val"  # encrypted
        assert user_token.access_secret != b"access_secret_val"


def test_user_token_record_validation(mock_app: Flask) -> None:
    with mock_app.app_context():
        user = UserRecord(user_id=456, username="model_validation_user")
        db.session.add(user)
        db.session.commit()

        user_token = UserTokenRecord(user_id=456, access_token=bytearray(b"token"), access_secret=memoryview(b"secret"))
        assert isinstance(user_token.access_token, bytes)
        assert isinstance(user_token.access_secret, bytes)
