from __future__ import annotations

from src.main_app.jobs_workers.utils import generate_result_file_name


def test_generate_result_file_name():
    assert generate_result_file_name(1, "test") == "test_job_1.json"
    assert generate_result_file_name(123, "my_job") == "my_job_job_123.json"
