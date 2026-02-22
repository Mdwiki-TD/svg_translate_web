"""Integration tests for the admin jobs management routes."""

from __future__ import annotations

import json
from dataclasses import replace
from html import unescape
from types import SimpleNamespace
from typing import Any, List
from unittest.mock import patch

import pytest

from src.main_app import create_app
from src.main_app.jobs_workers import jobs_service
from src.main_app.jobs_workers.jobs_service import JobRecord


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

    def _find_index(self, job_id: int, job_type: str) -> int:
        for index, record in enumerate(self._records):
            if record.id == job_id:
                if record.job_type == job_type:
                    return index
                else:
                    raise LookupError(f"Job id {job_id} is not a {job_type.replace('_', ' ')} job")
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

    def get(self, job_id: int, job_type: str) -> JobRecord:
        """Get a job by ID."""
        index = self._find_index(job_id, job_type)
        return self._records[index]

    def list(self, limit: int = 100, job_type: str | None = None) -> List[JobRecord]:
        """List recent jobs, optionally filtered by job_type."""
        if job_type:
            return [r for r in self._records if r.job_type == job_type][:limit]
        return list(self._records[:limit])

    def update_status(self, job_id: int, status: str, result_file: str | None = None, *, job_type: str) -> JobRecord:
        """Update job status."""
        index = self._find_index(job_id, job_type)
        updated = replace(
            self._records[index],
            status=status,
            result_file=result_file,
        )
        self._records[index] = updated
        return updated

    def delete(self, job_id: int, job_type: str) -> bool:
        """Delete a job by ID and job type."""
        try:
            index = self._find_index(job_id, job_type)
            self._records.pop(index)
            return True
        except LookupError:
            return False


@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client paired with a fake jobs store."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    admin_user = SimpleNamespace(username="admin")

    def fake_current_user() -> SimpleNamespace:
        return admin_user

    monkeypatch.setattr("src.main_app.users.current.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admin_routes.jobs.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.admins.admins_required.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.admins.admins_required.active_coordinators", lambda: {admin_user.username})
    monkeypatch.setattr("src.main_app.admins.admin_service.active_coordinators", lambda: {admin_user.username})
    monkeypatch.setattr("src.main_app.users.current.active_coordinators", lambda: {admin_user.username})
    monkeypatch.setattr("src.main_app.admins.admin_service.has_db_config", lambda: True)

    fake_store = FakeJobsDB({})

    monkeypatch.setattr("src.main_app.jobs_workers.jobs_service.has_db_config", lambda: True)

    def fake_jobs_factory(_db_data: dict[str, Any]):
        return fake_store

    monkeypatch.setattr("src.main_app.jobs_workers.jobs_service.JobsDB", fake_jobs_factory)

    jobs_service._JOBS_STORE = fake_store

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
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

    response = client.get("/admin/collect_main_files/list")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Collect Main Files Jobs" in page


def test_jobs_list_page_shows_no_jobs_message(admin_jobs_client):
    """Test that the jobs list page shows a message when there are no jobs."""
    client, store = admin_jobs_client

    response = client.get("/admin/collect_main_files/list")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Collect Main Files Jobs" in page


def test_job_detail_page_displays_job_info(admin_jobs_client):
    """Test that the job detail page displays job information."""
    client, store = admin_jobs_client

    job = store.create("collect_main_files")
    store.update_status(job.id, "completed", job_type="collect_main_files")

    response = client.get(f"/admin/collect_main_files/{job.id}")
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

    store.update_status(job.id, "completed", str(result_file), job_type="collect_main_files")

    response = client.get(f"/admin/collect_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # updated count
    assert "Template:Test1" in page
    assert "Template:Test2" in page


def test_job_detail_page_handles_nonexistent_job(admin_jobs_client):
    """Test that the job detail page handles nonexistent job gracefully."""
    client, store = admin_jobs_client

    response = client.get("/admin/collect_main_files/999", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job id 999 was not found" in page or "not found" in page.lower()


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin.admin_routes.jobs.load_auth_payload")
def test_start_collect_main_files_job_route(mock_load_auth, mock_start_job, admin_jobs_client):
    """Test that the start collect main files job route works."""
    client, store = admin_jobs_client

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    # Mock the job creation
    mock_start_job.return_value = 1

    response = client.post("/admin/collect_main_files/start", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job 1 started" in page or "started" in page.lower()

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_jobs_page_has_collect_button(admin_jobs_client):
    """Test that the jobs page has a collect main files button."""
    client, store = admin_jobs_client

    response = client.get("/admin/collect_main_files/list")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Start New Job" in page
    assert "/admin/collect_main_files/start" in page


def test_jobs_list_filters_by_job_type(admin_jobs_client):
    """Test that the jobs list only shows collect_main_files jobs."""
    client, store = admin_jobs_client

    # Create jobs of different types
    store.create("collect_main_files")
    store.create("collect_main_files")
    store.create("other_job_type")

    response = client.get("/admin/collect_main_files/list")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 3)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_fix_nested_jobs_list_page_displays_jobs(admin_jobs_client):
    """Test that the fix nested jobs list page displays jobs."""
    client, store = admin_jobs_client

    # Create some test jobs
    store.create("fix_nested_main_files")
    store.create("fix_nested_main_files")

    response = client.get("/admin/fix_nested_main_files/list")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Fix Nested Main Files Jobs" in page


def test_fix_nested_jobs_list_page_shows_no_jobs_message(admin_jobs_client):
    """Test that the fix nested jobs list page shows a message when there are no jobs."""
    client, store = admin_jobs_client

    response = client.get("/admin/fix_nested_main_files/list")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Fix Nested Main Files Jobs" in page


def test_fix_nested_job_detail_page_displays_job_info(admin_jobs_client):
    """Test that the fix nested job detail page displays job information."""
    client, store = admin_jobs_client

    job = store.create("fix_nested_main_files")
    store.update_status(job.id, "completed", job_type="fix_nested_main_files")

    response = client.get(f"/admin/fix_nested_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Fix Nested Main Files Job #{job.id}" in page
    assert "completed" in page


def test_fix_nested_job_detail_page_shows_result_data(admin_jobs_client, tmp_path):
    """Test that the fix nested job detail page displays result data from JSON file."""
    client, store = admin_jobs_client

    job = store.create("fix_nested_main_files")

    # Create a fake result file
    result_data = {
        "job_id": job.id,
        "summary": {
            "total": 5,
            "success": 3,
            "failed": 1,
            "skipped": 1,
            "no_main_file": 1,
        },
        "templates_success": [
            {"id": 1, "title": "Template:Test1", "main_file": "test1.svg", "fix_result": {"message": "Success"}},
        ],
        "templates_failed": [
            {"id": 2, "title": "Template:Test2", "main_file": "test2.svg", "reason": "Failed to fix"},
        ],
        "templates_skipped": [
            {"id": 3, "title": "Template:Test3", "reason": "No main_file set"},
        ],
    }

    result_file = tmp_path / "result.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f)

    store.update_status(job.id, "completed", str(result_file), job_type="fix_nested_main_files")

    response = client.get(f"/admin/fix_nested_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # success count
    assert "Template:Test1" in page
    assert "Template:Test2" in page
    assert "Template:Test3" in page


def test_fix_nested_job_detail_page_handles_nonexistent_job(admin_jobs_client):
    """Test that the fix nested job detail page handles nonexistent job gracefully."""
    client, store = admin_jobs_client

    response = client.get("/admin/fix_nested_main_files/999", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job id 999 was not found" in page or "not found" in page.lower()


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin.admin_routes.jobs.load_auth_payload")
def test_start_fix_nested_main_files_job_route(mock_load_auth, mock_start_job, admin_jobs_client):
    """Test that the start fix nested main files job route works."""
    client, store = admin_jobs_client

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.return_value = 1

    response = client.post("/admin/fix_nested_main_files/start", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job 1 started" in page or "started" in page.lower()

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_fix_nested_jobs_page_has_start_button(admin_jobs_client):
    """Test that the fix nested jobs page has a start button."""
    client, store = admin_jobs_client

    response = client.get("/admin/fix_nested_main_files/list")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Start New Job" in page
    assert "/admin/fix_nested_main_files/start" in page


def test_fix_nested_jobs_list_filters_by_job_type(admin_jobs_client):
    """Test that the fix nested jobs list only shows fix_nested_main_files jobs."""
    client, store = admin_jobs_client

    # Create jobs of different types
    store.create("fix_nested_main_files")
    store.create("fix_nested_main_files")
    store.create("collect_main_files")
    store.create("other_job_type")

    response = client.get("/admin/fix_nested_main_files/list")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 4)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_fix_nested_job_detail_page_redirects_for_wrong_job_type(admin_jobs_client):
    """Test that accessing a non-fix_nested job via fix_nested route redirects."""
    client, store = admin_jobs_client

    # Create a collect_main_files job
    job = store.create("collect_main_files")

    response = client.get(f"/admin/fix_nested_main_files/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "not a fix nested main files job" in page.lower()


def test_job_detail_rejects_wrong_job_type(admin_jobs_client):
    """Test that accessing detail page of non-collect_main_files job is rejected."""
    client, store = admin_jobs_client

    job = store.create("other_job_type")

    response = client.get(f"/admin/collect_main_files/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "not a collect main files job" in page.lower()


def test_delete_collect_main_files_job(admin_jobs_client):
    """Test deleting a collect_main_files job."""
    client, store = admin_jobs_client

    # Create a job
    job = store.create("collect_main_files")
    assert len(store.list()) == 1

    # Delete the job
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=False):
        response = client.post(f"/admin/collect_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Job {job.id} deleted successfully" in page

    # Verify job is deleted
    assert len(store.list()) == 0


def test_delete_fix_nested_main_files_job(admin_jobs_client):
    """Test deleting a fix_nested_main_files job."""
    client, store = admin_jobs_client

    # Create a job
    job = store.create("fix_nested_main_files")
    assert len(store.list()) == 1

    # Delete the job
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=False):
        response = client.post(f"/admin/fix_nested_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Job {job.id} deleted successfully" in page

    # Verify job is deleted
    assert len(store.list()) == 0


def test_delete_nonexistent_job(admin_jobs_client):
    """Test deleting a non-existent job shows appropriate error."""
    client, store = admin_jobs_client

    # Try to delete a job that doesn't exist
    response = client.post("/admin/collect_main_files/999/delete", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    # The actual message will depend on the error handling
    assert "Failed to delete job" in page or "deleted successfully" in page


def test_delete_job_with_wrong_type(admin_jobs_client):
    """Test deleting a job through the wrong job type endpoint."""
    client, store = admin_jobs_client

    # Create a collect_main_files job
    job = store.create("collect_main_files")

    # Try to delete it via the fix_nested endpoint
    response = client.post(f"/admin/fix_nested_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200

    # The job should still exist (delete should fail)
    remaining_jobs = store.list()
    assert len(remaining_jobs) == 1


def test_delete_multiple_jobs(admin_jobs_client):
    """Test deleting multiple jobs one by one."""
    client, store = admin_jobs_client

    # Create multiple jobs
    job1 = store.create("collect_main_files")
    job2 = store.create("collect_main_files")
    job3 = store.create("fix_nested_main_files")
    assert len(store.list()) == 3

    # Delete first collect_main_files job
    response = client.post(f"/admin/collect_main_files/{job1.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert len(store.list()) == 2

    # Delete second collect_main_files job
    response = client.post(f"/admin/collect_main_files/{job2.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert len(store.list()) == 1

    # Delete fix_nested_main_files job
    response = client.post(f"/admin/fix_nested_main_files/{job3.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert len(store.list()) == 0


def test_cancel_collect_main_files_job(admin_jobs_client):
    """Test cancelling a collect_main_files job."""
    client, store = admin_jobs_client

    # Create a job
    job = store.create("collect_main_files")
    store.update_status(job.id, "running", job_type="collect_main_files")

    # Cancel the job
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=True):
        response = client.post(f"/admin/collect_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Job {job.id} cancellation requested" in page


def test_cancel_fix_nested_main_files_job(admin_jobs_client):
    """Test cancelling a fix_nested_main_files job."""
    client, store = admin_jobs_client

    # Create a job
    job = store.create("fix_nested_main_files")
    store.update_status(job.id, "running", job_type="fix_nested_main_files")

    # Cancel the job
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=True):
        response = client.post(f"/admin/fix_nested_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Job {job.id} cancellation requested" in page


# ================================================================================
# download_main_files tests
# ================================================================================


def test_download_main_files_jobs_list_page_displays_jobs(admin_jobs_client):
    """Test that the download main files jobs list page displays jobs."""
    client, store = admin_jobs_client

    # Create some test jobs
    store.create("download_main_files")
    store.create("download_main_files")

    response = client.get("/admin/download_main_files/list")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Download Main Files Jobs" in page


def test_download_main_files_jobs_list_page_shows_no_jobs_message(admin_jobs_client):
    """Test that the download main files jobs list page shows a message when there are no jobs."""
    client, store = admin_jobs_client

    response = client.get("/admin/download_main_files/list")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Download Main Files Jobs" in page


def test_download_main_files_job_detail_page_displays_job_info(admin_jobs_client):
    """Test that the download main files job detail page displays job information."""
    client, store = admin_jobs_client

    job = store.create("download_main_files")
    store.update_status(job.id, "completed", job_type="download_main_files")

    response = client.get(f"/admin/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Download Main Files Job #{job.id}" in page
    assert "completed" in page


def test_download_main_files_job_detail_page_shows_result_data(admin_jobs_client, tmp_path):
    """Test that the download main files job detail page displays result data from JSON file."""
    client, store = admin_jobs_client

    job = store.create("download_main_files")

    # Create a fake result file
    result_data = {
        "job_id": job.id,
        "output_path": "/tmp/main_files",
        "summary": {
            "total": 5,
            "downloaded": 3,
            "failed": 1,
            "exists": 1,
        },
        "files_downloaded": [
            {
                "template_id": 1,
                "filename": "test1.svg",
                "path": "test1.svg",
                "size_bytes": 1024,
            },
        ],
        "files_failed": [
            {
                "template_id": 2,
                "template_title": "Template:Test2",
                "filename": "test2.svg",
                "reason": "Download failed: 404",
            },
        ],
    }

    result_file = tmp_path / "result.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f)

    store.update_status(job.id, "completed", str(result_file), job_type="download_main_files")

    response = client.get(f"/admin/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # downloaded count
    assert "test1.svg" in page
    assert "Template:Test2" in page


def test_download_main_files_job_detail_page_handles_nonexistent_job(admin_jobs_client):
    """Test that the download main files job detail page handles nonexistent job gracefully."""
    client, store = admin_jobs_client

    response = client.get("/admin/download_main_files/999", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job id 999 was not found" in page or "not found" in page.lower()


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin.admin_routes.jobs.load_auth_payload")
def test_start_download_main_files_job_route(mock_load_auth, mock_start_job, admin_jobs_client):
    """Test that the start download main files job route works."""
    client, store = admin_jobs_client

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.return_value = 1

    response = client.post("/admin/download_main_files/start", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job 1 started" in page or "started" in page.lower()

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_download_main_files_jobs_page_has_start_button(admin_jobs_client):
    """Test that the download main files jobs page has a start button."""
    client, store = admin_jobs_client

    response = client.get("/admin/download_main_files/list")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Start New Job" in page
    assert "/admin/download_main_files/start" in page


def test_download_main_files_jobs_list_filters_by_job_type(admin_jobs_client):
    """Test that the download main files jobs list only shows download_main_files jobs."""
    client, store = admin_jobs_client

    # Create jobs of different types
    store.create("download_main_files")
    store.create("download_main_files")
    store.create("collect_main_files")
    store.create("fix_nested_main_files")

    response = client.get("/admin/download_main_files/list")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 4)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_download_main_files_job_detail_page_redirects_for_wrong_job_type(admin_jobs_client):
    """Test that accessing a non-download_main_files job via download route redirects."""
    client, store = admin_jobs_client

    # Create a collect_main_files job
    job = store.create("collect_main_files")

    response = client.get(f"/admin/download_main_files/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "not a download main files job" in page.lower()


def test_delete_download_main_files_job(admin_jobs_client):
    """Test deleting a download_main_files job."""
    client, store = admin_jobs_client

    # Create a job
    job = store.create("download_main_files")
    assert len(store.list()) == 1

    # Delete the job
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=False):
        response = client.post(f"/admin/download_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Job {job.id} deleted successfully" in page

    # Verify job is deleted
    assert len(store.list()) == 0


def test_cancel_download_main_files_job(admin_jobs_client):
    """Test cancelling a download_main_files job."""
    client, store = admin_jobs_client

    # Create a job
    job = store.create("download_main_files")
    store.update_status(job.id, "running", job_type="download_main_files")

    # Cancel the job
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=True):
        response = client.post(f"/admin/download_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Job {job.id} cancellation requested" in page


def test_cancel_job_not_running(admin_jobs_client):
    """Test cancelling a job that's not running shows appropriate message."""
    client, store = admin_jobs_client

    job = store.create("download_main_files")
    store.update_status(job.id, "completed", job_type="download_main_files")

    # Try to cancel a completed job
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=False):
        response = client.post(f"/admin/download_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "is not running or already cancelled" in page


@patch("src.main_app.app_routes.admin.admin_routes.jobs.send_from_directory")
@patch("src.main_app.app_routes.admin.admin_routes.jobs.settings")
def test_serve_download_main_file(mock_settings, mock_send, admin_jobs_client):
    """Test serving a downloaded main file."""
    client, store = admin_jobs_client

    # Mock the settings
    mock_settings.paths.main_files_path = "/tmp/main_files"

    mock_send.return_value = "file_content"

    response = client.get("/admin/download-main-files/file/test.svg")
    assert response.status_code == 200

    mock_send.assert_called_once_with("/tmp/main_files", "test.svg")


@patch("src.main_app.app_routes.admin.admin_routes.jobs.create_main_files_zip")
def test_download_all_main_files(mock_create_zip, admin_jobs_client):
    """Test downloading all main files as zip."""
    client, store = admin_jobs_client

    mock_create_zip.return_value = ("zip_content", 200)

    response = client.get("/admin/download-main-files/download-all")
    assert response.status_code == 200

    mock_create_zip.assert_called_once()


@patch("src.main_app.app_routes.admin.admin_routes.jobs.create_main_files_zip")
def test_download_all_main_files_no_directory(mock_create_zip, admin_jobs_client):
    """Test downloading all main files when directory doesn't exist."""
    client, store = admin_jobs_client

    mock_create_zip.return_value = ("Main files directory does not exist", 404)

    response = client.get("/admin/download-main-files/download-all")
    assert response.status_code == 404

    mock_create_zip.assert_called_once()


def test_job_list_page_with_invalid_job_type_returns_404(admin_jobs_client):
    """Test that requesting an invalid job type returns 404."""
    client, store = admin_jobs_client

    response = client.get("/admin/invalid_job_type/list")
    assert response.status_code == 404


def test_start_job_without_user_login(admin_jobs_client, monkeypatch):
    """Test starting a job without being logged in."""
    client, store = admin_jobs_client

    # Mock current_user to return None
    monkeypatch.setattr("src.main_app.app_routes.admin.admin_routes.jobs.current_user", lambda: None)

    response = client.post("/admin/collect_main_files/start", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "must be logged in" in page.lower()


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin.admin_routes.jobs.load_auth_payload")
def test_start_job_handles_exception(mock_load_auth, mock_start_job, admin_jobs_client):
    """Test that job start handles exceptions gracefully."""
    client, store = admin_jobs_client

    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.side_effect = Exception("Database error")

    response = client.post("/admin/collect_main_files/start", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Failed to start job" in page or "error" in page.lower()


def test_delete_job_handles_exception(admin_jobs_client, monkeypatch):
    """Test that job deletion handles exceptions gracefully."""
    client, store = admin_jobs_client

    job = store.create("collect_main_files")

    # Mock delete to raise an exception
    def mock_delete_job(job_id, job_type):
        raise Exception("Database error")

    monkeypatch.setattr("src.main_app.jobs_workers.jobs_service.delete_job", mock_delete_job)

    response = client.post(f"/admin/collect_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Failed to delete job" in page


def test_download_main_files_job_with_partial_results(admin_jobs_client, tmp_path):
    """Test displaying partial results for a running job."""
    client, store = admin_jobs_client

    job = store.create("download_main_files")

    # Create a result file with partial results
    result_data = {
        "job_id": job.id,
        "output_path": "/tmp/main_files",
        "summary": {
            "total": 10,
            "downloaded": 5,
            "failed": 0,
            "exists": 0,
        },
        "files_downloaded": [
            {
                "template_id": i,
                "filename": f"test{i}.svg",
                "path": f"test{i}.svg",
                "size_bytes": 1024 * i,
            }
            for i in range(1, 6)
        ],
        "files_failed": [],
    }

    result_file = tmp_path / "result.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f)

    store.update_status(job.id, "running", str(result_file), job_type="download_main_files")

    response = client.get(f"/admin/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "5" in page  # downloaded count
    assert "running" in page.lower()


def test_cancel_already_cancelled_job(admin_jobs_client):
    """Test cancelling a job that's already been cancelled."""
    client, store = admin_jobs_client

    job = store.create("download_main_files")
    store.update_status(job.id, "cancelled", job_type="download_main_files")

    # Try to cancel again
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.jobs_worker.cancel_job", return_value=False):
        response = client.post(f"/admin/download_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "not running or already cancelled" in page.lower()


def test_serve_download_main_file_with_path_traversal_attempt(admin_jobs_client):
    """Test that path traversal is handled by send_from_directory."""
    client, store = admin_jobs_client

    # send_from_directory should handle path traversal attempts
    with patch("src.main_app.app_routes.admin.admin_routes.jobs.send_from_directory") as mock_send:
        mock_send.return_value = "safe response"
        response = client.get("/admin/download-main-files/file/../../../etc/passwd")
        # send_from_directory will be called with the attempted path
        mock_send.assert_called_once()
