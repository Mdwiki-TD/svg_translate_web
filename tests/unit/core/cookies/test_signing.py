"""Unit tests for auth.signing module.

Tests for cookie signing and verification helpers.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from src.main_app.services.core.cookies.signing import SignedTokenService


class TestSignUserId:
    """Tests for sign_user_id function."""

    def test_signs_integer_user_id(self):
        """Test that integer user ID is signed correctly."""
        signed = SignedTokenService().sign_user_id(12345)

        assert isinstance(signed, str)
        assert len(signed) > 0

    def test_produces_different_signatures_for_different_ids(self):
        """Test that different user IDs produce different signatures."""
        signed1 = SignedTokenService().sign_user_id(1)
        signed2 = SignedTokenService().sign_user_id(2)

        assert signed1 != signed2

    def test_produces_consistent_signature_for_same_id(self):
        """Test that same user ID produces consistent signatures (within same secret)."""
        signed1 = SignedTokenService().sign_user_id(12345)
        signed2 = SignedTokenService().sign_user_id(12345)

        # Both should be valid and extract to same ID
        assert SignedTokenService().extract_user_id(signed1) == SignedTokenService().extract_user_id(signed2) == 12345


class TestExtractUserId:
    """Tests for extract_user_id function."""

    def test_extracts_correct_user_id(self):
        """Test that user ID is extracted correctly from valid token."""
        original_id = 12345
        signed = SignedTokenService().sign_user_id(original_id)

        extracted = SignedTokenService().extract_user_id(signed)

        assert extracted == original_id

    def test_returns_none_for_invalid_token(self):
        """Test that None is returned for invalid token."""
        result = SignedTokenService().extract_user_id("invalid.token.here")

        assert result is None

    def test_returns_none_for_empty_string(self):
        """Test that None is returned for empty string."""
        result = SignedTokenService().extract_user_id("")

        assert result is None

    def test_returns_none_for_malformed_data(self, monkeypatch):
        """Test that None is returned when data doesn't contain uid."""
        # Create a token with wrong data structure

        signed = SignedTokenService().dump_uid({"wrong_key": 12345})

        result = SignedTokenService().extract_user_id(signed)

        assert result is None

    def test_returns_none_for_non_integer_uid(self, monkeypatch):
        """Test that None is returned when uid is not an integer."""

        signed = SignedTokenService().dump_uid({"uid": "not_an_integer"})

        result = SignedTokenService().extract_user_id(signed)

        assert result is None

    def test_returns_none_for_expired_token(self, monkeypatch):
        """Test that None is returned for expired token."""
        # Create a token
        signed = SignedTokenService().sign_user_id(12345)

        # Patch max_age to be -1 to expire immediately
        # (itsdangerous uses age > max_age check, so -1 expires all tokens)
        with patch("src.main_app.services.core.cookies.signing.get_settings") as mock_settings:
            mock_settings.return_value.cookie.max_age = -1  # Expire immediately

            result = SignedTokenService().extract_user_id(signed)
            # Should return None for expired token
            assert result is None


class TestSignStateToken:
    """Tests for sign_state_token function."""

    def test_signs_state_nonce(self):
        """Test that state nonce is signed correctly."""
        nonce = "random_state_nonce_123"
        signed = SignedTokenService().sign_state_token(nonce)

        assert isinstance(signed, str)
        assert len(signed) > 0

    def test_produces_different_signatures_for_different_nonces(self):
        """Test that different nonces produce different signatures."""
        signed1 = SignedTokenService().sign_state_token("nonce1")
        signed2 = SignedTokenService().sign_state_token("nonce2")

        assert signed1 != signed2


class TestVerifyStateToken:
    """Tests for verify_state_token function."""

    def test_verifies_valid_token(self):
        """Test that valid token is verified and nonce returned."""
        original_nonce = "state_nonce_123"
        signed = SignedTokenService().sign_state_token(original_nonce)

        verified = SignedTokenService().verify_state_token(signed)

        assert verified == original_nonce

    def test_returns_none_for_invalid_token(self):
        """Test that None is returned for invalid token."""
        result = SignedTokenService().verify_state_token("invalid.token.here")

        assert result is None

    def test_returns_none_for_empty_string(self):
        """Test that None is returned for empty string."""
        result = SignedTokenService().verify_state_token("")

        assert result is None

    def test_returns_none_when_nonce_missing(self, monkeypatch):
        """Test that None is returned when nonce is missing from data."""

        signed = SignedTokenService().dump_state({"wrong_key": "value"})

        result = SignedTokenService().verify_state_token(signed)

        assert result is None

    def test_returns_none_when_nonce_not_string(self, monkeypatch):
        """Test that None is returned when nonce is not a string."""

        signed = SignedTokenService().dump_state({"nonce": 12345})

        result = SignedTokenService().verify_state_token(signed)

        assert result is None


class TestRoundTrip:
    """Tests for sign/verify round-trip scenarios."""

    @pytest.mark.parametrize(
        "user_id",
        [
            1,
            12345,
            999999,
            0,
        ],
    )
    def test_user_id_round_trip(self, user_id):
        """Test that user IDs round-trip correctly."""
        signed = SignedTokenService().sign_user_id(user_id)
        extracted = SignedTokenService().extract_user_id(signed)

        assert extracted == user_id

    @pytest.mark.parametrize(
        "nonce",
        [
            "simple_nonce",
            "nonce-with-dashes",
            "nonce_with_underscores",
            "12345",
            "a" * 100,  # Long nonce
        ],
    )
    def test_state_token_round_trip(self, nonce):
        """Test that state nonces round-trip correctly."""
        signed = SignedTokenService().sign_state_token(nonce)
        verified = SignedTokenService().verify_state_token(signed)

        assert verified == nonce
