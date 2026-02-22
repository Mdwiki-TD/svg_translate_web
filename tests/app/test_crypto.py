"""Unit tests for cryptographic helpers."""

from src.app.crypto import decrypt_value, encrypt_value


def test_encrypt_decrypt_roundtrip():
    msg = "secret message"
    token = encrypt_value(msg)
    assert isinstance(token, (bytes, bytearray))
    plain = decrypt_value(token)
    assert plain == msg
