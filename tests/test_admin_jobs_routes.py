"""Integration tests for the admin jobs management routes."""

from __future__ import annotations

from dataclasses import replace
from html import unescape
from types import SimpleNamespace
from typing import Any, List
from unittest.mock import MagicMock, patch
import json
import tempfile

import pytest

from src.app import create_app, jobs_service
from src.app.jobs_service import JobRecord


class FakeJobsDB:
    """In-memory replacement for the MySQL-backed JobsDB helper."""

    def __init__(self, _db_data: dict[str, Any] | None = None):
        del _db_data
        self._records: list[JobRecord] = []
        self._next_id = 1

    # -- helpers -----------------------------------------------------------------
    def reset(self) -> None:
        self._records.clear()
        self._next_id = 1

    def _find_index(self, job_id: int) -> int:
        for index, record in enumerate(self._records):
            if record.id == job_id:
                return index
        raise LookupError(f"Job id {job_id} was not found")

    def create(self, job_type: str) -> JobRecord:
        """Create a new job."""
        record = JobRecord(
            id=self._next_id,
            job_type=job_type,
            status="pending",
        )
        self._records.append(record)
        self._next_id += 1
        return record

    def get(self, job_id: int) -> JobRecord:
        """Get a job by ID."""
        index = self._find_index(job_id)
        return self._records[index]

    def list(self, limit: int = 100) -> List[JobRecord]:
        """List recent jobs."""
        return list(self._records[:limit])

    def update_status(
        self, job_id: int, status: str, result_file: str | None = None
    ) -> JobRecord:
        """Update job status."""
        index = self._find_index(job_id)
        updated = replace(
            self._records[index],
            status=status,
            result_file=result_file,
        )
        self._records[index] = updated
        return updated


@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client paired with a fake jobs store."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    admin_user = SimpleNamespace(username="admin")

    def fake_current_user() -> SimpleNamespace:
        return admin_user

    monkeypatch.setattr("src.app.users.current.current_user", fake_current_user)
    monkeypatch.setattr(
        "src.app.app_routes.admin.admin_routes.jobs.current_user", fake_current_user
    )
    monkeypatch.setattr("src.app.app_routes.admin.admins_required.current_user", fake_current_user)
    monkeypatch.setattr(
        "src.app.app_routes.admin.admins_required.active_coordinators", lambda: {admin_user.username}
    )
    monkeypatch.setattr(
        "src.app.users.admin_service.active_coordinators", lambda: {admin_user.username}
    )
    monkeypatch.setattr(
        "src.app.users.current.active_coordinators", lambda: {admin_user.username}
    )
    monkeypatch.setattr("src.app.users.admin_service.has_db_config", lambda: True)

    fake_store = FakeJobsDB({})

    monkeypatch.setattr("src.app.jobs_service.has_db_config", lambda: True)

    def fake_jobs_factory(_db_data: dict[str, Any]):
        return fake_store

    monkeypatch.setattr("src.app.jobs_service.JobsDB", fake_jobs_factory)

    jobs_service._JOBS_STORE = fake_store

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    try:
        yield client, fake_store
    finally:
        jobs_service._JOBS_STORE = None
        fake_store.reset()


def test_jobs_list_page_displays_jobs(admin_jobs_client):
    """Test that the jobs list page displays jobs."""
    client, store = admin_jobs_client

    # Create some test jobs
    store.create("collect_main_files")
    store.create("collect_main_files")

    response = client.get("/admin/collect-main-files-jobs")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Collect Main Files Jobs" in page


def test_jobs_list_page_shows_no_jobs_message(admin_jobs_client):
    """Test that the jobs list page shows a message when there are no jobs."""
    client, store = admin_jobs_client

    response = client.get("/admin/collect-main-files-jobs")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "No jobs found" in page


def test_job_detail_page_displays_job_info(admin_jobs_client):
    """Test that the job detail page displays job information."""
    client, store = admin_jobs_client

    job = store.create("collect_main_files")
    store.update_status(job.id, "completed")

    response = client.get(f"/admin/collect-main-files-jobs/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Collect Main Files Job #{job.id}" in page
    assert "completed" in page


def test_job_detail_page_shows_result_data(admin_jobs_client, tmp_path):
    """Test that the job detail page displays result data from JSON file."""
    client, store = admin_jobs_client

    job = store.create("collect_main_files")
    
    # Create a fake result file
    result_data = {
        "job_id": job.id,
        "summary": {
            "total": 5,
            "updated": 3,
            "failed": 1,
            "skipped": 1,
        },
        "templates_updated": [
            {"id": 1, "title": "Template:Test1", "new_main_file": "test1.svg"},
        ],
        "templates_failed": [
            {"id": 2, "title": "Template:Test2", "reason": "No wikitext found"},
        ],
    }
    
    result_file = tmp_path / "result.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f)
    
    store.update_status(job.id, "completed", str(result_file))

    response = client.get(f"/admin/collect-main-files-jobs/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # updated count
    assert "Template:Test1" in page
    assert "Template:Test2" in page


def test_job_detail_page_handles_nonexistent_job(admin_jobs_client):
    """Test that the job detail page handles nonexistent job gracefully."""
    client, store = admin_jobs_client

    response = client.get("/admin/collect-main-files-jobs/999", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job id 999 was not found" in page or "not found" in page.lower()


@patch("src.app.jobs_worker.start_collect_main_files_job")
def test_start_collect_main_files_job_route(mock_start_job, admin_jobs_client):
    """Test that the start collect main files job route works."""
    client, store = admin_jobs_client
    
    # Mock the job creation
    mock_start_job.return_value = 1

    response = client.post("/admin/collect-main-files-jobs/start", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job 1 started" in page or "started" in page.lower()
    
    mock_start_job.assert_called_once()


def test_jobs_page_has_collect_button(admin_jobs_client):
    """Test that the jobs page has a collect main files button."""
    client, store = admin_jobs_client

    response = client.get("/admin/collect-main-files-jobs")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Start New Job" in page
    assert "/admin/collect-main-files-jobs/start" in page


def test_jobs_list_filters_by_job_type(admin_jobs_client):
    """Test that the jobs list only shows collect_main_files jobs."""
    client, store = admin_jobs_client

    # Create jobs of different types
    store.create("collect_main_files")
    store.create("collect_main_files")
    store.create("other_job_type")
    
    response = client.get("/admin/collect-main-files-jobs")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    
    # Should show 2 rows of jobs (not 3)
    # Count the number of "View" buttons which appear once per job row
    assert page.count('btn btn-outline-primary btn-sm') == 2


def test_job_detail_rejects_wrong_job_type(admin_jobs_client):
    """Test that accessing detail page of non-collect_main_files job is rejected."""
    client, store = admin_jobs_client

    job = store.create("other_job_type")
    
    response = client.get(f"/admin/collect-main-files-jobs/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "not a collect main files job" in page.lower()
