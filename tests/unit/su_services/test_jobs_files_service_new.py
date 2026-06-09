"""Unit tests for jobs_files_service."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.su_services.jobs_files_service import (
    create_job_cancelled_file,
    get_jobs_data_dir,
    is_job_cancelled_file_exist,
    load_job_result,
    save_job_result_by_name,
)


@pytest.fixture
def mock_settings(tmp_path):
    with patch("src.main_app.su_services.jobs_files_service.settings") as m_settings:
        m_settings.paths.jobs_path = str(tmp_path / "jobs")
        get_jobs_data_dir.cache_clear()
        yield m_settings


def test_get_jobs_data_dir_no_path():
    with patch("src.main_app.su_services.jobs_files_service.settings") as m_settings:
        m_settings.paths.jobs_path = None
        get_jobs_data_dir.cache_clear()
        with pytest.raises(RuntimeError, match="jobs_path configuration is required"):
            get_jobs_data_dir()


def test_save_job_result_by_name(mock_settings, tmp_path):
    data = {"status": "ok"}
    path = save_job_result_by_name("test.json", data)
    assert path.name == "test.json"
    assert path.exists()
    with open(path, "r") as f:
        assert json.load(f) == data


def test_load_job_result_success(mock_settings, tmp_path):
    data = {"status": "loaded"}
    path = Path(mock_settings.paths.jobs_path)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "load.json", "w") as f:
        json.dump(data, f)

    res = load_job_result("load.json")
    assert res == data


def test_load_job_result_not_found(mock_settings):
    assert load_job_result("missing.json") is None


def test_load_job_result_error(mock_settings):
    path = Path(mock_settings.paths.jobs_path)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "bad.json", "w") as f:
        f.write("invalid json")
    assert load_job_result("bad.json") is None


def test_create_job_cancelled_file_success(mock_settings):
    path = create_job_cancelled_file("job.cancel")
    assert path.exists()
    assert path.read_text() == "cancelled"


def test_create_job_cancelled_file_error(mock_settings):
    # Make directory read-only to provoke OSError
    path = Path(mock_settings.paths.jobs_path)
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o444)
    try:
        res = create_job_cancelled_file("job.cancel")
        assert res is None
    finally:
        path.chmod(0o777)


def test_is_job_cancelled_file_exist(mock_settings):
    path = Path(mock_settings.paths.jobs_path)
    path.mkdir(parents=True, exist_ok=True)
    cancel_file = path / "exist.cancel"
    cancel_file.touch()

    assert is_job_cancelled_file_exist("exist.cancel") is True
    assert is_job_cancelled_file_exist("no.cancel") is False


def test_is_job_cancelled_file_exist_error(mock_settings):
    with patch("src.main_app.su_services.jobs_files_service.Path.exists") as m_exists:
        m_exists.side_effect = OSError("Access denied")
        assert is_job_cancelled_file_exist("any.cancel") is False
