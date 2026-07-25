from __future__ import annotations

from unittest.mock import patch

import pytest

from src.main_app.su_services.jobs_files_service import (
    get_jobs_data_dir,
    load_job_result,
)


@pytest.fixture
def temp_jobs_dir(tmp_path):
    with patch("src.main_app.su_services.jobs_files_service.settings") as mock_settings:
        mock_settings.paths.public_jobs_path = str(tmp_path)
        get_jobs_data_dir.cache_clear()
        yield tmp_path


def test_load_job_result_non_existent(temp_jobs_dir):
    assert load_job_result("missing.json") is None


def test_load_job_result_invalid_json(temp_jobs_dir):
    file = temp_jobs_dir / "bad.json"
    file.write_text("not json")
    assert load_job_result("bad.json") is None
