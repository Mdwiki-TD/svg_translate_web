"""Tests for users store module."""

import pytest

from src.main_app.shared.decode_bytes import coerce_bytes


class TestCoerceBytes:
    """Tests for coerce_bytes function."""

    def test_coerce_bytes_with_bytes(self):
        """Test coerce_bytes with bytes input."""
        input_bytes = b"test_data"
        result = coerce_bytes(input_bytes)
        assert result == input_bytes

    def test_coerce_bytes_with_bytearray(self):
        """Test coerce_bytes with bytearray input."""
        input_bytearray = bytearray(b"test_data")
        result = coerce_bytes(input_bytearray)
        assert result == b"test_data"
        assert isinstance(result, bytes)

    def test_coerce_bytes_with_memoryview(self):
        """Test coerce_bytes with memoryview input."""
        input_memoryview = memoryview(b"test_data")
        result = coerce_bytes(input_memoryview)
        assert result == b"test_data"
        assert isinstance(result, bytes)

    def test_coerce_bytes_with_invalid_type(self):
        """Test coerce_bytes raises TypeError for invalid input."""
        with pytest.raises(TypeError, match="Expected bytes-compatible value"):
            coerce_bytes("string_not_bytes")

    def test_coerce_bytes_with_int(self):
        """Test coerce_bytes raises TypeError for integer input."""
        with pytest.raises(TypeError, match="Expected bytes-compatible value"):
            coerce_bytes(123)

    def test_coerce_bytes_with_none(self):
        """Test coerce_bytes raises TypeError for None input."""
        with pytest.raises(TypeError, match="Expected bytes-compatible value"):
            coerce_bytes(None)
