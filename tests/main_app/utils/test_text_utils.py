"""Tests for text_utils module."""

import logging

import pytest

from src.main_app.utils.text_utils import ensure_file_prefix, verify_required_fields


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


class TestVerifyRequiredFields:
    """Tests for verify_required_fields function."""

    def test_all_fields_present(self):
        """Test when all required fields have values."""
        fields = {
            "field1": "value1",
            "field2": 123,
            "field3": ["item"],
        }
        result = verify_required_fields(fields)
        assert result == []

    def test_empty_fields_list(self):
        """Test with empty fields dictionary."""
        result = verify_required_fields({})
        assert result == []

    def test_single_missing_field(self):
        """Test when one field is missing (None)."""
        fields = {
            "field1": "value1",
            "field2": None,
        }
        result = verify_required_fields(fields)
        assert result == ["field2"]

    def test_multiple_missing_fields(self):
        """Test when multiple fields are missing."""
        fields = {
            "field1": None,
            "field2": "",
            "field3": [],
            "field4": 0,
            "field5": False,
            "field6": "value6",
        }
        result = verify_required_fields(fields)
        assert "field1" in result
        assert "field2" in result
        assert "field3" in result
        assert "field4" in result
        assert "field5" in result
        assert "field6" not in result
        assert len(result) == 5

    def test_empty_string_considered_missing(self):
        """Test that empty string is considered missing."""
        fields = {"field1": ""}
        result = verify_required_fields(fields)
        assert result == ["field1"]

    def test_empty_list_considered_missing(self):
        """Test that empty list is considered missing."""
        fields = {"field1": []}
        result = verify_required_fields(fields)
        assert result == ["field1"]

    def test_zero_considered_missing(self):
        """Test that 0 is considered missing (falsy value)."""
        fields = {"field1": 0}
        result = verify_required_fields(fields)
        assert result == ["field1"]

    def test_false_considered_missing(self):
        """Test that False is considered missing (falsy value)."""
        fields = {"field1": False}
        result = verify_required_fields(fields)
        assert result == ["field1"]

    def test_whitespace_not_considered_missing(self):
        """Test that whitespace string is truthy and not missing."""
        fields = {"field1": "   "}
        result = verify_required_fields(fields)
        assert result == []

    def test_logs_error_for_missing_fields(self, caplog):
        """Test that errors are logged for missing fields."""
        with caplog.at_level(logging.ERROR):
            fields = {"missing_field": None}
            verify_required_fields(fields)

        assert "Missing required field: missing_field" in caplog.text

    def test_logs_multiple_errors(self, caplog):
        """Test that errors are logged for each missing field."""
        with caplog.at_level(logging.ERROR):
            fields = {
                "field1": None,
                "field2": "",
            }
            verify_required_fields(fields)

        assert "Missing required field: field1" in caplog.text
        assert "Missing required field: field2" in caplog.text
