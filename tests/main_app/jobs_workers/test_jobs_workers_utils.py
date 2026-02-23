"""Unit tests for utils module."""

from __future__ import annotations

from src.main_app.jobs_workers.utils import generate_result_file_name


def test_generate_result_file_name():
    """Test generate_result_file_name creates correct filename."""
    filename = generate_result_file_name(123, "test_job")

    assert filename == "test_job_job_123.json"
