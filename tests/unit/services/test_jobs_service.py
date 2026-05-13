"""Unit tests for jobs_service module."""

from __future__ import annotations

import json

# import tempfile
# from unittest.mock import MagicMock, patch
from pathlib import Path
from typing import Any

import pytest

from src.main_app.db.db_Jobs import JobRecord
from src.main_app.jobs_workers.jobs_files_service import (
    get_jobs_data_dir,
    load_job_result,
    save_job_result,
    save_job_result_by_name,
)
from src.main_app.jobs_workers.utils import generate_result_file_name
from src.main_app.services import jobs_service
from src.main_app.services.jobs_service import (
    create_job,
    delete_job,
    get_job,
    get_jobs_db,
    list_jobs,
    update_job_status,
)


class FakeJobsDB:
    """In-memory replacement for the MySQL-backed JobsDB helper."""

    def __init__(self, _db_data: dict[str, Any] | None = None):
        del _db_data
        self._records: list[JobRecord] = []
        self._next_id = 1

    def create(self, job_type: str, username: str | None = None) -> JobRecord:
        record = JobRecord(
            id=self._next_id,
            job_type=job_type,
            status="pending",
            username=username,
        )
        self._records.append(record)
        self._next_id += 1
        return record

    def get(self, job_id: int, job_type: str) -> JobRecord:
        for record in self._records:
            if record.id == job_id and record.job_type == job_type:
                return record
        raise LookupError(f"Job id {job_id} of type {job_type} was not found")

    def delete(self, job_id: int, job_type: str) -> bool:
        """Delete a job by ID and job type."""
        for i, record in enumerate(self._records):
            if record.id == job_id and record.job_type == job_type:
                self._records.pop(i)
                return True
        return False

    def list(self, limit: int = 100, job_type: str | None = None) -> list[JobRecord]:
        if job_type:
            return [r for r in self._records if r.job_type == job_type][:limit]
        return list(self._records[:limit])

    def update_status(self, job_id: int, status: str, result_file: str | None = None, *, job_type: str) -> JobRecord:
        for record in self._records:
            if record.id == job_id and record.job_type == job_type:
                record.status = status
                record.result_file = result_file
                return record
        raise LookupError(f"Job id {job_id} of type {job_type} was not found")


@pytest.fixture
def jobs_db_fixture(monkeypatch: pytest.MonkeyPatch):
    """Set up a fake jobs database."""
    fake_store = FakeJobsDB({})

    monkeypatch.setattr("src.main_app.services.jobs_service.has_db_config", lambda: True)

    def fake_jobs_factory(_db_data: dict[str, Any]):
        return fake_store

    monkeypatch.setattr("src.main_app.services.jobs_service.JobsDB", fake_jobs_factory)

    jobs_service._JOBS_STORE = None  # Reset global state

    try:
        yield fake_store
    finally:
        jobs_service._JOBS_STORE = None


def test_create_job(jobs_db_fixture):
    """Test creating a new job."""
    job = create_job("collect_main_files")

    assert job is not None
    assert job.id == 1
    assert job.job_type == "collect_main_files"
    assert job.status == "pending"


def test_create_job_with_username(jobs_db_fixture):
    """Test creating a new job with username."""
    job = create_job("collect_main_files", username="test_user")

    assert job is not None
    assert job.id == 1
    assert job.job_type == "collect_main_files"
    assert job.status == "pending"
    assert job.username == "test_user"


def test_get_job(jobs_db_fixture):
    """Test retrieving a job by ID."""
    created_job = create_job("collect_main_files")

    retrieved_job = get_job(created_job.id, job_type="collect_main_files")

    assert retrieved_job.id == created_job.id
    assert retrieved_job.job_type == created_job.job_type


def test_get_nonexistent_job(jobs_db_fixture):
    """Test retrieving a nonexistent job raises LookupError."""
    with pytest.raises(LookupError, match="Job id 999 of type collect_main_files was not found"):
        get_job(999, job_type="collect_main_files")


def test_list_jobs(jobs_db_fixture):
    """Test listing jobs."""
    create_job("collect_main_files")
    create_job("collect_main_files")
    create_job("other_job")

    jobs = list_jobs()

    assert len(jobs) == 3
    assert all(isinstance(job, JobRecord) for job in jobs)


def test_list_jobs_with_limit(jobs_db_fixture):
    """Test listing jobs with a limit."""
    for _ in range(5):
        create_job("collect_main_files")

    jobs = list_jobs(limit=2)

    assert len(jobs) == 2


def test_update_job_status(jobs_db_fixture):
    """Test updating a job's status."""
    job = create_job("collect_main_files")

    updated_job = update_job_status(job.id, "running", job_type="collect_main_files")

    assert updated_job.status == "running"


def test_update_job_status_with_result_file(jobs_db_fixture):
    """Test updating a job's status with a result file."""
    job = create_job("collect_main_files")

    updated_job = update_job_status(job.id, "completed", "/path/to/result.json", job_type="collect_main_files")

    assert updated_job.status == "completed"
    assert updated_job.result_file == "/path/to/result.json"


def test_load_nonexistent_job_result():
    """Test loading a nonexistent job result returns None."""
    loaded_data = load_job_result("/nonexistent/file.json")

    assert loaded_data is None


def test_delete_job(jobs_db_fixture):
    """Test deleting a job."""
    job = create_job("collect_main_files")
    assert len(jobs_service.list_jobs()) == 1

    delete_job(job.id, "collect_main_files")

    assert len(jobs_service.list_jobs()) == 0


def test_delete_job_with_correct_type(jobs_db_fixture):
    """Test deleting a job with correct job type."""
    job1 = create_job("collect_main_files")
    job2 = create_job("fix_nested_main_files")
    assert len(jobs_service.list_jobs()) == 2

    delete_job(job1.id, "collect_main_files")

    remaining_jobs = list_jobs()
    assert len(remaining_jobs) == 1
    assert remaining_jobs[0].id == job2.id


def test_delete_job_with_wrong_type(jobs_db_fixture):
    """Test deleting a job with wrong job type doesn't delete it."""
    job = create_job("collect_main_files")
    assert len(jobs_service.list_jobs()) == 1

    # Try to delete with wrong job type
    delete_job(job.id, "fix_nested_main_files")

    # Job should still exist
    remaining_jobs = list_jobs()
    assert len(remaining_jobs) == 1
    assert remaining_jobs[0].id == job.id


def test_delete_nonexistent_job(jobs_db_fixture):
    """Test deleting a non-existent job."""
    # Should not raise an error
    delete_job(999, "collect_main_files")

    # No jobs should exist
    assert len(jobs_service.list_jobs()) == 0


def test_list_jobs_filtered_by_type(jobs_db_fixture):
    """Test listing jobs filtered by job_type."""
    create_job("collect_main_files")
    create_job("collect_main_files")
    create_job("fix_nested_main_files")
    create_job("other_job_type")

    # Filter by collect_main_files
    collect_jobs = list_jobs(job_type="collect_main_files")
    assert len(collect_jobs) == 2
    assert all(job.job_type == "collect_main_files" for job in collect_jobs)

    # Filter by fix_nested_main_files
    fix_jobs = list_jobs(job_type="fix_nested_main_files")
    assert len(fix_jobs) == 1
    assert all(job.job_type == "fix_nested_main_files" for job in fix_jobs)

    # No filter - should return all
    all_jobs = list_jobs()
    assert len(all_jobs) == 4


def test_list_jobs_filtered_with_limit(jobs_db_fixture):
    """Test listing jobs filtered by job_type with a limit."""
    for _ in range(5):
        create_job("collect_main_files")
    for _ in range(3):
        create_job("fix_nested_main_files")

    # Filter by type with limit
    collect_jobs = list_jobs(limit=2, job_type="collect_main_files")
    assert len(collect_jobs) == 2
    assert all(job.job_type == "collect_main_files" for job in collect_jobs)


def test_get_jobs_db_no_config(monkeypatch: pytest.MonkeyPatch):
    """Test get_jobs_db raises error when DB config is missing."""
    monkeypatch.setattr("src.main_app.services.jobs_service.has_db_config", lambda: False)
    _JOBS_STORE = None

    with pytest.raises(RuntimeError, match="Jobs administration requires database configuration"):
        get_jobs_db()

    _JOBS_STORE = None


def test_get_jobs_db_cached(jobs_db_fixture):
    """Test get_jobs_db returns cached instance."""
    db1 = get_jobs_db()
    db2 = get_jobs_db()

    assert db1 is db2


def test_update_job_status_nonexistent(jobs_db_fixture):
    """Test updating status of a nonexistent job raises LookupError."""
    with pytest.raises(LookupError):
        update_job_status(999, "completed", job_type="test_job")
