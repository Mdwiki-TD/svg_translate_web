"""
Tests for cookie helpers.
src/main_app/shared/core/cookies/cookie.py
"""

from __future__ import annotations

from src.main_app.shared.core.cookies.cookie import (
    _serializer,
    _state_serializer,
    extract_user_id,
    sign_state_token,
    sign_user_id,
    verify_state_token,
)


def test_sign_user_id() -> None:
    token = sign_user_id(123)

    data = _serializer.loads(token)
    assert data["uid"] == 123


def test_extract_user_id_valid_token() -> None:
    token = _serializer.dumps({"uid": 55})

    assert extract_user_id(token) == 55


def test_sign_state_token() -> None:
    token = sign_state_token("nonce")

    data = _state_serializer.loads(token)
    assert data["nonce"] == "nonce"


def test_verify_state_token_success() -> None:
    token = _state_serializer.dumps({"nonce": "abc"})

    assert verify_state_token(token) == "abc"


def test_verify_state_token_invalid_payload() -> None:
    token = _state_serializer.dumps({"not": "nonce"})

    assert verify_state_token(token) is None


def test_extract_user_id_invalid_token() -> None:
    assert extract_user_id("invalid-token") is None


def test_verify_state_token_bad_signature() -> None:
    assert verify_state_token("bad-token") is None


class TestSignAndExtractUserId:
    def test_round_trip(self):
        token = sign_user_id(42)
        assert isinstance(token, str)
        assert extract_user_id(token) == 42

    def test_different_ids(self):
        token1 = sign_user_id(1)
        token2 = sign_user_id(2)
        assert extract_user_id(token1) == 1
        assert extract_user_id(token2) == 2

    def test_invalid_token_returns_none(self):
        assert extract_user_id("not-a-valid-token") is None

    def test_empty_token_returns_none(self):
        assert extract_user_id("") is None

    def test_tampered_token_returns_none(self):
        token = sign_user_id(42)
        assert extract_user_id(token + "tamper") is None


class TestSignAndVerifyStateToken:
    def test_round_trip(self):
        token = sign_state_token("my-nonce-123")
        assert isinstance(token, str)
        assert verify_state_token(token) == "my-nonce-123"

    def test_invalid_token_returns_none(self):
        assert verify_state_token("invalid") is None

    def test_different_nonces(self):
        t1 = sign_state_token("nonce1")
        t2 = sign_state_token("nonce2")
        assert verify_state_token(t1) == "nonce1"
        assert verify_state_token(t2) == "nonce2"
