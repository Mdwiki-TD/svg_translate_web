"""Tests for text_utils module."""

from src.main_app.utils.text_utils import ensure_file_prefix


class TestEnsureFilePrefix:
    """Tests for ensure_file_prefix function."""

    def test_adds_prefix_when_missing(self):
        """Test that File: prefix is added when missing."""
        result = ensure_file_prefix("Example.svg")
        assert result == "File:Example.svg"

    def test_does_not_add_prefix_when_present(self):
        """Test that File: prefix is not added when already present."""
        result = ensure_file_prefix("File:Example.svg")
        assert result == "File:Example.svg"

    def test_handles_empty_string(self):
        """Test handling of empty string."""
        result = ensure_file_prefix("")
        assert result == "File:"

    def test_handles_prefix_with_different_case(self):
        """Test that only exact 'File:' prefix is recognized."""
        # "file:" (lowercase) should get prefix added
        result = ensure_file_prefix("file:Example.svg")
        assert result == "File:file:Example.svg"

    def test_handles_prefix_in_middle(self):
        """Test that File: in the middle doesn't count as prefix."""
        result = ensure_file_prefix("Example_File:test.svg")
        assert result == "File:Example_File:test.svg"
