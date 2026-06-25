"""Unit tests for src/main_app/core/crypto.py module."""

from __future__ import annotations

import pytest

from src.main_app.shared.core.crypto import decrypt_value, encrypt_value


def test_encrypt_decrypt_roundtrip():
    msg = "secret message"
    token = encrypt_value(msg)
    assert isinstance(token, bytes | bytearray)
    plain = decrypt_value(token)
    assert plain == msg


class TestEncryptDecrypt:
    def test_round_trip(self):
        plaintext = "hello world"
        token = encrypt_value(plaintext)
        assert isinstance(token, bytes)
        assert decrypt_value(token) == plaintext

    def test_empty_string(self):
        token = encrypt_value("")
        assert decrypt_value(token) == ""

    def test_unicode_content(self):
        plaintext = "Ünïcödé 日本語"
        token = encrypt_value(plaintext)
        assert decrypt_value(token) == plaintext

    def test_long_string(self):
        plaintext = "A" * 10_000
        token = encrypt_value(plaintext)
        assert decrypt_value(token) == plaintext

    def test_encrypted_is_different_from_plaintext(self):
        plaintext = "secret-oauth-token"
        token = encrypt_value(plaintext)
        assert plaintext.encode() not in token

    def test_decrypt_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Unable to decrypt"):
            decrypt_value(b"not-a-valid-fernet-token")

    def test_different_encryptions_produce_different_tokens(self):
        """Fernet uses a random IV, so same input should give different ciphertext."""
        plaintext = "same-value"
        token1 = encrypt_value(plaintext)
        token2 = encrypt_value(plaintext)
        assert token1 != token2
        assert decrypt_value(token1) == decrypt_value(token2)
