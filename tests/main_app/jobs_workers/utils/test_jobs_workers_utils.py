"""
Tests for src/main_app/jobs_workers/utils.py
"""

from __future__ import annotations

from src.main_app.jobs_workers.utils import generate_result_file_name


def test_generate_result_file_name():
    """Test generate_result_file_name creates correct filename."""
    filename = generate_result_file_name(123, "test_job")

    assert filename == "test_job_job_123.json"


class TestGenerateResultFileName:
    """Tests for the generate_result_file_name function."""

    def test_generate_result_file_name_basic(self) -> None:
        """Test generate_result_file_name with basic inputs."""
        result = generate_result_file_name(123, "download_main_files")
        assert result == "download_main_files_job_123.json"

    def test_generate_result_file_name_string_job_id(self) -> None:
        """Test generate_result_file_name with string job_id."""
        result = generate_result_file_name("abc-123", "crop_main_files")
        assert result == "crop_main_files_job_abc-123.json"

    def test_generate_result_file_name_different_job_types(self) -> None:
        """Test generate_result_file_name with different job types."""
        job_types = [
            "collect_main_files",
            "create_owid_pages",
            "crop_main_files",
            "download_main_files",
            "fix_nested_main_files",
        ]

        for job_type in job_types:
            result = generate_result_file_name(1, job_type)
            assert result == f"{job_type}_job_1.json"

    def test_generate_result_file_name_zero_job_id(self) -> None:
        """Test generate_result_file_name with job_id of 0."""
        result = generate_result_file_name(0, "test_job")
        assert result == "test_job_job_0.json"

    def test_generate_result_file_name_empty_job_type(self) -> None:
        """Test generate_result_file_name with empty job_type."""
        result = generate_result_file_name(123, "")
        assert result == "_job_123.json"
