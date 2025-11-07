"""Tests for cookie helpers."""

from __future__ import annotations

import types

import pytest
from itsdangerous import URLSafeTimedSerializer

from src.app.app_routes.auth import cookie


@pytest.fixture(autouse=True)
def configure_serializers(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cookie = types.SimpleNamespace(max_age=3600)
    fake_settings = types.SimpleNamespace(secret_key="secret", cookie=fake_cookie)
    serializer = URLSafeTimedSerializer(fake_settings.secret_key, salt="svg-translate-uid")
    state_serializer = URLSafeTimedSerializer(fake_settings.secret_key, salt="svg-translate-oauth-state")

    monkeypatch.setattr(cookie, "settings", fake_settings)
    monkeypatch.setattr(cookie, "_serializer", serializer)
    monkeypatch.setattr(cookie, "_state_serializer", state_serializer)


def test_sign_user_id() -> None:
    token = cookie.sign_user_id(123)

    data = cookie._serializer.loads(token)
    assert data["uid"] == 123


def test_extract_user_id_valid_token() -> None:
    token = cookie._serializer.dumps({"uid": 55})

    assert cookie.extract_user_id(token) == 55


def test_extract_user_id_invalid_token() -> None:
    assert cookie.extract_user_id("invalid-token") is None


def test_sign_state_token() -> None:
    token = cookie.sign_state_token("nonce")

    data = cookie._state_serializer.loads(token)
    assert data["nonce"] == "nonce"


def test_verify_state_token_success() -> None:
    token = cookie._state_serializer.dumps({"nonce": "abc"})

    assert cookie.verify_state_token(token) == "abc"


def test_verify_state_token_invalid_payload() -> None:
    token = cookie._state_serializer.dumps({"not": "nonce"})

    assert cookie.verify_state_token(token) is None


def test_verify_state_token_bad_signature() -> None:
    assert cookie.verify_state_token("bad-token") is None
