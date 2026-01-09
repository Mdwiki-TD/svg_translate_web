"""Unit tests for jobs_service module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.app import jobs_service
from src.app.jobs_service import JobRecord


class FakeJobsDB:
    """In-memory replacement for the MySQL-backed JobsDB helper."""

    def __init__(self, _db_data: dict[str, Any] | None = None):
        del _db_data
        self._records: list[JobRecord] = []
        self._next_id = 1

    def create(self, job_type: str) -> JobRecord:
        record = JobRecord(
            id=self._next_id,
            job_type=job_type,
            status="pending",
        )
        self._records.append(record)
        self._next_id += 1
        return record

    def get(self, job_id: int) -> JobRecord:
        for record in self._records:
            if record.id == job_id:
                return record
        raise LookupError(f"Job id {job_id} was not found")

    def list(self, limit: int = 100) -> list[JobRecord]:
        return list(self._records[:limit])

    def update_status(
        self, job_id: int, status: str, result_file: str | None = None
    ) -> JobRecord:
        for record in self._records:
            if record.id == job_id:
                record.status = status
                record.result_file = result_file
                return record
        raise LookupError(f"Job id {job_id} was not found")


@pytest.fixture
def jobs_db_fixture(monkeypatch: pytest.MonkeyPatch):
    """Set up a fake jobs database."""
    fake_store = FakeJobsDB({})

    monkeypatch.setattr("src.app.jobs_service.has_db_config", lambda: True)

    def fake_jobs_factory(_db_data: dict[str, Any]):
        return fake_store

    monkeypatch.setattr("src.app.jobs_service.JobsDB", fake_jobs_factory)

    jobs_service._JOBS_STORE = None  # Reset global state

    try:
        yield fake_store
    finally:
        jobs_service._JOBS_STORE = None


def test_create_job(jobs_db_fixture):
    """Test creating a new job."""
    job = jobs_service.create_job("collect_main_files")
    
    assert job is not None
    assert job.id == 1
    assert job.job_type == "collect_main_files"
    assert job.status == "pending"


def test_get_job(jobs_db_fixture):
    """Test retrieving a job by ID."""
    created_job = jobs_service.create_job("collect_main_files")
    
    retrieved_job = jobs_service.get_job(created_job.id)
    
    assert retrieved_job.id == created_job.id
    assert retrieved_job.job_type == created_job.job_type


def test_get_nonexistent_job(jobs_db_fixture):
    """Test retrieving a nonexistent job raises LookupError."""
    with pytest.raises(LookupError, match="Job id 999 was not found"):
        jobs_service.get_job(999)


def test_list_jobs(jobs_db_fixture):
    """Test listing jobs."""
    jobs_service.create_job("collect_main_files")
    jobs_service.create_job("collect_main_files")
    jobs_service.create_job("other_job")
    
    jobs = jobs_service.list_jobs()
    
    assert len(jobs) == 3
    assert all(isinstance(job, JobRecord) for job in jobs)


def test_list_jobs_with_limit(jobs_db_fixture):
    """Test listing jobs with a limit."""
    for _ in range(5):
        jobs_service.create_job("collect_main_files")
    
    jobs = jobs_service.list_jobs(limit=2)
    
    assert len(jobs) == 2


def test_update_job_status(jobs_db_fixture):
    """Test updating a job's status."""
    job = jobs_service.create_job("collect_main_files")
    
    updated_job = jobs_service.update_job_status(job.id, "running")
    
    assert updated_job.status == "running"


def test_update_job_status_with_result_file(jobs_db_fixture):
    """Test updating a job's status with a result file."""
    job = jobs_service.create_job("collect_main_files")
    
    updated_job = jobs_service.update_job_status(
        job.id, "completed", "/path/to/result.json"
    )
    
    assert updated_job.status == "completed"
    assert updated_job.result_file == "/path/to/result.json"


def test_save_job_result(jobs_db_fixture, tmp_path, monkeypatch):
    """Test saving a job result to a JSON file."""
    # Mock get_jobs_data_dir to use tmp_path
    monkeypatch.setattr("src.app.jobs_service.get_jobs_data_dir", lambda: tmp_path)
    
    job = jobs_service.create_job("collect_main_files")
    
    result_data = {
        "job_id": job.id,
        "summary": {
            "total": 5,
            "updated": 3,
        },
    }
    
    result_file = jobs_service.save_job_result(job.id, result_data)
    
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
    
    loaded_data = jobs_service.load_job_result(str(result_file))
    
    assert loaded_data is not None
    assert loaded_data["job_id"] == 1
    assert loaded_data["summary"]["total"] == 5


def test_load_nonexistent_job_result():
    """Test loading a nonexistent job result returns None."""
    loaded_data = jobs_service.load_job_result("/nonexistent/file.json")
    
    assert loaded_data is None


def test_load_job_result_with_invalid_json(tmp_path):
    """Test loading an invalid JSON file returns None."""
    result_file = tmp_path / "invalid.json"
    with open(result_file, "w") as f:
        f.write("not valid json")
    
    loaded_data = jobs_service.load_job_result(str(result_file))
    
    assert loaded_data is None
