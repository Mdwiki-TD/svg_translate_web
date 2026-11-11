"""Unit tests for crypto module.

Tests for encryption/decryption helpers used for OAuth token storage.
"""

from __future__ import annotations

import pytest
from src.main_app.services.core.crypto import CryptoService


@pytest.fixture
def crypto_service():
    return CryptoService()


class TestEncryptValue:
    """Tests for CryptoService.encrypt function."""

    def test_encrypts_string_to_bytes(self, crypto_service: CryptoService) -> None:
        """Test that a string is encrypted to bytes."""
        original: str = "test_secret_value"
        encrypted: bytes = crypto_service.encrypt(original)

        assert isinstance(encrypted, bytes)
        assert encrypted != original.encode()

    def test_encrypts_unicode_string(self, crypto_service: CryptoService) -> None:
        """Test that unicode strings are handled correctly."""
        original: str = "héllo wörld 日本語"
        encrypted: bytes = crypto_service.encrypt(original)

        assert isinstance(encrypted, bytes)
        # Should be able to decrypt back
        decrypted: str = crypto_service.decrypt(encrypted)
        assert decrypted == original

    def test_encrypts_empty_string(self, crypto_service: CryptoService) -> None:
        """Test that empty string can be encrypted."""
        original: str = ""
        encrypted: bytes = crypto_service.encrypt(original)

        assert isinstance(encrypted, bytes)
        decrypted: str = crypto_service.decrypt(encrypted)
        assert decrypted == original

    def test_produces_different_tokens_for_same_input(self, crypto_service: CryptoService) -> None:
        """Test that encrypting same value produces different tokens (due to timestamp)."""
        original: str = "test_value"
        encrypted1: bytes = crypto_service.encrypt(original)
        encrypted2: bytes = crypto_service.encrypt(original)

        # Tokens should be different due to timestamp
        assert encrypted1 != encrypted2
        # But both should decrypt to same value
        assert crypto_service.decrypt(encrypted1) == crypto_service.decrypt(encrypted2) == original


class TestDecryptValue:
    """Tests for CryptoService.decrypt function."""

    def test_decrypts_to_original_value(self, crypto_service: CryptoService) -> None:
        """Test that decryption returns original value."""
        original: str = "my_secret_token"
        encrypted: bytes = crypto_service.encrypt(original)
        decrypted: str = crypto_service.decrypt(encrypted)

        assert decrypted == original

    def test_decrypts_unicode(self, crypto_service: CryptoService) -> None:
        """Test decryption of unicode strings."""
        original: str = "héllo wörld 🎉"
        encrypted: bytes = crypto_service.encrypt(original)
        decrypted: str = crypto_service.decrypt(encrypted)

        assert decrypted == original

    def test_raises_on_invalid_token(self, crypto_service: CryptoService) -> None:
        """Test that invalid token raises ValueError."""
        invalid_token: bytes = b"invalid_token_bytes"

        with pytest.raises(ValueError, match="Unable to decrypt stored token"):
            crypto_service.decrypt(invalid_token)

    def test_raises_on_tampered_token(self, crypto_service: CryptoService) -> None:
        """Test that tampered token raises ValueError."""
        original: str = "test_value"
        encrypted: bytes = crypto_service.encrypt(original)

        # Tamper with the token
        tampered: bytes = encrypted[:-5] + b"xxxxx"

        with pytest.raises(ValueError, match="Unable to decrypt stored token"):
            crypto_service.decrypt(tampered)

    def test_raises_on_empty_bytes(self, crypto_service: CryptoService) -> None:
        """Test that empty bytes raises ValueError."""
        with pytest.raises(ValueError, match="Unable to decrypt stored token"):
            crypto_service.decrypt(b"")


class TestRoundTrip:
    """Tests for encrypt/decrypt round-trip scenarios."""

    @pytest.mark.parametrize(
        "original",
        [
            "simple_string",
            "string_with_special_chars!@#$%",
            "unicode_日本語",
            "long_string_" * 10,
            "",
            "single_token_with_underscores_and-dashes123",
        ],
    )
    def test_various_strings_round_trip(self, crypto_service, original: str) -> None:
        """Test that various string types round-trip correctly."""
        encrypted: bytes = crypto_service.encrypt(original)
        decrypted: str = crypto_service.decrypt(encrypted)
        assert decrypted == original

    def test_oauth_token_like_values(self, crypto_service: CryptoService) -> None:
        """Test with values that resemble OAuth tokens."""
        # Simulate OAuth access token and secret
        access_token: str = "abcdefghijklmnop1234567890"
        access_secret: str = "secret_value_with_special_chars+/="

        encrypted_token: bytes = crypto_service.encrypt(access_token)
        encrypted_secret: bytes = crypto_service.encrypt(access_secret)

        assert crypto_service.decrypt(encrypted_token) == access_token
        assert crypto_service.decrypt(encrypted_secret) == access_secret
