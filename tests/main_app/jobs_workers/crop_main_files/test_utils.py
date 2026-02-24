"""Tests for crop_main_files/utils module."""

import pytest

from src.main_app.jobs_workers.crop_main_files.utils import generate_cropped_filename


class TestGenerateCroppedFilename:
    """Tests for generate_cropped_filename function."""

    def test_basic_filename_with_file_prefix(self):
        """Test transforming filename with File: prefix."""
        result = generate_cropped_filename("File:test.svg")
        assert result == "File:test (cropped).svg"

    def test_basic_filename_without_file_prefix(self):
        """Test transforming filename without File: prefix."""
        result = generate_cropped_filename("test.svg")
        assert result == "File:test (cropped).svg"

    def test_filename_with_spaces(self):
        """Test transforming filename with spaces."""
        result = generate_cropped_filename("File:death rate from obesity, World, 2021.svg")
        assert result == "File:death rate from obesity, World, 2021 (cropped).svg"

    def test_filename_with_multiple_dots(self):
        """Test transforming filename with multiple dots."""
        result = generate_cropped_filename("File:chart.v2.test.svg")
        assert result == "File:chart.v2.test (cropped).svg"

    def test_filename_with_different_extension(self):
        """Test transforming filename with different extension."""
        result = generate_cropped_filename("File:image.png")
        assert result == "File:image (cropped).png"

    def test_filename_without_extension(self):
        """Test transforming filename without extension."""
        result = generate_cropped_filename("File:readme")
        assert result == "File:readme (cropped)"

    def test_filename_with_underscores(self):
        """Test transforming filename with underscores."""
        result = generate_cropped_filename("File:my_test_file.svg")
        assert result == "File:my_test_file (cropped).svg"

    def test_empty_filename(self):
        """Test transforming empty filename."""
        result = generate_cropped_filename("")
        assert result == "File: (cropped)"

    def test_filename_with_only_file_prefix(self):
        """Test transforming filename with only File: prefix."""
        result = generate_cropped_filename("File:")
        assert result == "File: (cropped)"
