"""
Tests for services.utils.decode_bytes module.
"""

import pytest

from src.main_app.services.utils.decode_bytes import coerce_bytes


class TestCoerceBytes:
    """Tests for coerce_bytes function."""

    def test_returns_bytes_unchanged(self):
        """Test that bytes input is returned unchanged."""
        input_bytes = b"test_bytes"
        result = coerce_bytes(input_bytes)
        assert result == input_bytes

    def test_converts_bytearray_to_bytes(self):
        """Test that bytearray is converted to bytes."""
        input_bytearray = bytearray(b"test_bytes")
        result = coerce_bytes(input_bytearray)
        assert isinstance(result, bytes)
        assert result == b"test_bytes"

    def test_converts_memoryview_to_bytes(self):
        """Test that memoryview is converted to bytes."""
        input_memoryview = memoryview(b"test_bytes")
        result = coerce_bytes(input_memoryview)
        assert isinstance(result, bytes)
        assert result == b"test_bytes"

    def test_raises_on_invalid_type(self):
        """Test that invalid types raise TypeError."""
        with pytest.raises(TypeError, match="Expected bytes-compatible value"):
            coerce_bytes("string_not_allowed")

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
