"""Unit tests for cryptographic helpers."""
import pytest

from src.app.crypto import decrypt_value, encrypt_value, DecryptionError


def test_encrypt_decrypt_roundtrip():
    msg = "secret message"
    token = encrypt_value(msg)
    assert isinstance(token, (bytes, bytearray))
    plain = decrypt_value(token)
    assert plain == msg


def test_decrypt_invalid_token_raises():
    """Test that decrypting an invalid token raises DecryptionError."""
    with pytest.raises(DecryptionError):
        decrypt_value(b"not-a-valid-fernet-token")
