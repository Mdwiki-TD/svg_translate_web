from __future__ import annotations

from src.main_app.jobs_workers.utils import generate_result_file_name

class TestGenerateResultFileName:
    def test_basic(self):
        assert generate_result_file_name(1, "test") == "test_job_1.json"
        assert generate_result_file_name(1, "test") == "test_job_1.json"
        assert generate_result_file_name(123, "my_job") == "my_job_job_123.json"

    def test_different_ids(self):
        assert generate_result_file_name(42, "replace") == "replace_job_42.json"

    def test_different_types(self):
        assert generate_result_file_name(1, "fixref") == "fixref_job_1.json"
