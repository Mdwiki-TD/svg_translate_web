"""Tests for the user token persistence helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db import svg_db
from src.main_app.services import user_token_service


@pytest.fixture(autouse=True)
def reset_db(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(svg_db, "_db", None)


def test_mark_token_used_updates_last_used(monkeypatch):
    fake_db = MagicMock()
    monkeypatch.setattr(user_token_service, "get_db", lambda: fake_db)

    user_token_service.mark_token_used(12)

    fake_db.execute_query.assert_called_once()
    executed_sql = fake_db.execute_query.call_args[0][0]
    assert "last_used_at = CURRENT_TIMESTAMP" in executed_sql


def test_user_token_record_decrypted(monkeypatch):
    monkeypatch.setattr("src.main_app.shared.models.users_record.decrypt_value", lambda value: value.decode("utf-8"))

    record = user_token_service.UserTokenRecord(
        user_id=3,
        username="Tester",
        access_token=b"token",
        access_secret=b"secret",
    )

    decrypted = record.decrypted()

    assert decrypted == ("token", "secret")
