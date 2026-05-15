"""Unit tests for jobs_service module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.main_app.db.models.jobs import JobRecord
from src.main_app.jobs_workers.utils import generate_result_file_name
from src.main_app.su_services.jobs_files_service import (
    get_jobs_data_dir,
    load_job_result,
    save_job_result,
    save_job_result_by_name,
)


def test_save_job_result(tmp_path, monkeypatch):
    """Test saving a job result to a JSON file."""
    # Mock get_jobs_data_dir to use tmp_path
    monkeypatch.setattr("src.main_app.su_services.jobs_files_service.get_jobs_data_dir", lambda: tmp_path)

    job = JobRecord(id=1, job_type="collect_main_files", status="pending")

    result_data = {
        "job_id": job.id,
        "summary": {
            "total": 5,
            "updated": 3,
        },
    }

    result_file = generate_result_file_name(job.id, job.job_type)
    result_file = save_job_result_by_name(result_file, result_data)

    assert result_file is not None
    assert Path(result_file).exists()

    # Verify the content
    with open(result_file, "r") as f:
        saved_data = json.load(f)

    assert saved_data["job_id"] == job.id
    assert saved_data["summary"]["total"] == 5


def test_load_job_result(tmp_path):
    """Test loading a job result from a JSON file."""
    result_data = {
        "job_id": 1,
        "summary": {"total": 5},
    }

    result_file = tmp_path / "result.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f)

    loaded_data = load_job_result(str(result_file))

    assert loaded_data is not None
    assert loaded_data["job_id"] == 1
    assert loaded_data["summary"]["total"] == 5


def test_load_job_result_with_invalid_json(tmp_path):
    """Test loading an invalid JSON file returns None."""
    result_file = tmp_path / "invalid.json"
    with open(result_file, "w") as f:
        f.write("not valid json")

    loaded_data = load_job_result(str(result_file))

    assert loaded_data is None


def test_get_jobs_data_dir_not_configured(monkeypatch: pytest.MonkeyPatch):
    """Test get_jobs_data_dir raises error when svg_jobs_path is not configured."""
    from types import SimpleNamespace

    mock_settings = SimpleNamespace(paths=SimpleNamespace())

    monkeypatch.setattr("src.main_app.su_services.jobs_files_service.settings", mock_settings)
    get_jobs_data_dir.cache_clear()

    with pytest.raises(RuntimeError, match="MAIN_DIR/svg_jobs environment variable is required"):
        get_jobs_data_dir()

    get_jobs_data_dir.cache_clear()


def test_get_jobs_data_dir_creates_directory(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Test get_jobs_data_dir creates the directory if it doesn't exist."""
    from types import SimpleNamespace

    jobs_dir = tmp_path / "jobs"
    assert not jobs_dir.exists()

    mock_settings = SimpleNamespace(paths=SimpleNamespace(svg_jobs_path=str(jobs_dir)))
    monkeypatch.setattr("src.main_app.su_services.jobs_files_service.settings", mock_settings)
    get_jobs_data_dir.cache_clear()

    result = get_jobs_data_dir()

    assert result == jobs_dir
    assert jobs_dir.exists()
    get_jobs_data_dir.cache_clear()


def test_save_job_result_with_datetime(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Test saving a job result with datetime objects (default serialization)."""
    from datetime import datetime

    monkeypatch.setattr("src.main_app.su_services.jobs_files_service.get_jobs_data_dir", lambda: tmp_path)

    job = JobRecord(id=1, job_type="test_job", status="pending")

    result_data = {"job_id": job.id, "timestamp": datetime.now(), "data": "test"}

    result_file_name = generate_result_file_name(job.id, job.job_type)
    result_file = save_job_result_by_name(result_file_name, result_data)

    assert result_file.exists()


def test_save_job_result_simple(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Test save_job_result without by_name variant."""
    monkeypatch.setattr("src.main_app.su_services.jobs_files_service.get_jobs_data_dir", lambda: tmp_path)

    job = JobRecord(id=1, job_type="test_job", status="pending")

    result_data = {"test": "data"}

    result_file_name = save_job_result(job.id, result_data)

    assert result_file_name == f"job_{job.id}.json"
    assert (tmp_path / result_file_name).exists()


def test_load_nonexistent_job_result():
    """Test loading a nonexistent job result returns None."""
    loaded_data = load_job_result("/nonexistent/file.json")

    assert loaded_data is None
