"""Integration tests for the admin jobs management routes."""

from __future__ import annotations

import json
from html import unescape
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.db.services import jobs_service as _sqlalchemy_jobs_service
from src.main_app.extensions import db as _db


class _JobsStore:
    """Adapter bridging old JobsDB API to SQLAlchemy jobs_service functions."""

    def create(self, job_type, username="z"):
        return _sqlalchemy_jobs_service.create_job(job_type, username)

    def list(self, limit=100, job_type=None):
        return _sqlalchemy_jobs_service.list_jobs(limit, job_type)

    def update_status(self, job_id, status, result_file=None, *, job_type):
        return _sqlalchemy_jobs_service.update_job_status(job_id, status, result_file, job_type=job_type)

    def get(self, job_id, job_type):
        return _sqlalchemy_jobs_service.get_job(job_id, job_type)

    def delete(self, job_id, job_type):
        return _sqlalchemy_jobs_service.delete_job(job_id, job_type)

    def cancel(self, job_id, job_type=None):
        return _sqlalchemy_jobs_service.cancel_job_db(job_id, job_type)


@pytest.fixture
def jobs_db():
    return _JobsStore()


@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client paired with a fake jobs jobs_db."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    admin_user = SimpleNamespace(username="admin", is_active_admin=True)

    def fake_current_user() -> SimpleNamespace:
        return admin_user

    monkeypatch.setattr("src.main_app.app_routes.auth.utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admins_required.load_user", fake_current_user)
    monkeypatch.setattr(
        "src.main_app.app_routes.utils.routes_utils._is_admin",
        lambda user: bool(getattr(user, "is_active_admin", False)),
    )

    app = create_app(TestingConfig)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables)
        yield app.test_client()
        _db.session.remove()
        _db.metadata.drop_all(_db.engine, tables=real_tables)


def test_jobs_list_page_displays_jobs(admin_jobs_client, jobs_db):
    """Test that the jobs list page displays jobs."""

    # Create some test jobs (complete first before creating second of same type)
    job1 = jobs_db.create("collect_templates_data")
    jobs_db.update_status(job1.id, "completed", job_type="collect_templates_data")
    jobs_db.create("collect_templates_data")

    response = admin_jobs_client.get("/admin/jobs/collect_templates_data")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Collect Templates data Jobs" in page


def test_jobs_list_page_shows_no_jobs_message(admin_jobs_client, jobs_db):
    """Test that the jobs list page shows a message when there are no jobs."""

    response = admin_jobs_client.get("/admin/jobs/collect_templates_data")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Collect Templates data Jobs" in page


def test_job_detail_page_displays_job_info(admin_jobs_client, jobs_db):
    """Test that the job detail page displays job information."""

    job = jobs_db.create("collect_templates_data")
    jobs_db.update_status(job.id, "completed", job_type="collect_templates_data")

    response = admin_jobs_client.get(f"/admin/jobs/collect_templates_data/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Collect Templates data Job #{job.id}" in page
    assert "Completed" in page


def test_job_detail_page_shows_result_data(admin_jobs_client, jobs_db, tmp_path):
    """Test that the job detail page displays result data from JSON file."""

    job = jobs_db.create("collect_templates_data")

    # Create a fake result file
    result_data = {
        "job_id": job.id,
        "summary": {
            "total": 5,
            "updated": 3,
            "failed": 1,
            "skipped": 1,
        },
        "pages_updated": [
            {"id": 1, "title": "Template:Test1", "new_main_file": "test1.svg"},
        ],
        "pages_failed": [
            {"id": 2, "title": "Template:Test2", "reason": "No wikitext found"},
        ],
    }

    result_file = tmp_path / "result.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f)

    jobs_db.update_status(job.id, "completed", str(result_file), job_type="collect_templates_data")

    response = admin_jobs_client.get(f"/admin/jobs/collect_templates_data/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # updated count
    assert "Template:Test1" in page
    assert "Template:Test2" in page


def test_job_detail_page_handles_nonexistent_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test that the job detail page handles nonexistent job gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    response = admin_jobs_client.get("/admin/jobs/collect_templates_data/999", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Job id 999 was not found", "warning")


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin_routes.jobs.load_auth_payload")
def test_start_collect_templates_data_job_route(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that the start collect templates data job route works."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    # Mock the job creation
    mock_start_job.return_value = 1

    response = admin_jobs_client.post("/admin/jobs/collect_templates_data/start")
    assert response.status_code == 302
    mock_flash.assert_any_call("Job 1 started to collect_templates_data.", "success")

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_jobs_page_has_collect_button(admin_jobs_client, jobs_db):
    """Test that the jobs page has a collect templates data button."""

    response = admin_jobs_client.get("/admin/jobs/collect_templates_data")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'action="/admin/jobs/collect_templates_data/start"' in page
    assert 'type="submit"' in page


def test_jobs_list_filters_by_job_type(admin_jobs_client, jobs_db):
    """Test that the jobs list only shows collect_templates_data jobs."""

    # Create jobs of different types
    job1 = jobs_db.create("collect_templates_data")
    jobs_db.update_status(job1.id, "completed", job_type="collect_templates_data")
    jobs_db.create("collect_templates_data")
    jobs_db.create("other_job_type")

    response = admin_jobs_client.get("/admin/jobs/collect_templates_data")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 3)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_fix_nested_jobs_list_page_displays_jobs(admin_jobs_client, jobs_db):
    """Test that the fix nested jobs list page displays jobs."""

    # Create some test jobs (complete first before creating second of same type)
    job1 = jobs_db.create("fix_nested_main_files")
    jobs_db.update_status(job1.id, "completed", job_type="fix_nested_main_files")
    jobs_db.create("fix_nested_main_files")

    response = admin_jobs_client.get("/admin/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Fix Nested Main Files Jobs" in page


def test_fix_nested_jobs_list_page_shows_no_jobs_message(admin_jobs_client, jobs_db):
    """Test that the fix nested jobs list page shows a message when there are no jobs."""

    response = admin_jobs_client.get("/admin/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Fix Nested Main Files Jobs" in page


def test_fix_nested_job_detail_page_displays_job_info(admin_jobs_client, jobs_db):
    """Test that the fix nested job detail page displays job information."""

    job = jobs_db.create("fix_nested_main_files")
    jobs_db.update_status(job.id, "completed", job_type="fix_nested_main_files")

    response = admin_jobs_client.get(f"/admin/jobs/fix_nested_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Fix Nested Main Files Job #{job.id}" in page
    assert "Completed" in page


def test_fix_nested_job_detail_page_shows_result_data(admin_jobs_client, jobs_db, tmp_path):
    """Test that the fix nested job detail page displays result data from JSON file."""

    job = jobs_db.create("fix_nested_main_files")

    # Create a fake result file
    result_data = {
        "job_id": job.id,
        "summary": {
            "total": 5,
            "success": 3,
            "failed": 1,
            "skipped": 1,
        },
        "pages_success": [
            {"id": 1, "title": "Template:Test1", "main_file": "test1.svg", "fix_result": {"message": "Success"}},
        ],
        "pages_failed": [
            {"id": 2, "title": "Template:Test2", "main_file": "test2.svg", "reason": "Failed to fix"},
        ],
        "pages_skipped": [
            {"id": 3, "title": "Template:Test3", "reason": "No main_file set"},
        ],
    }

    result_file = tmp_path / "result.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f)

    jobs_db.update_status(job.id, "completed", str(result_file), job_type="fix_nested_main_files")

    response = admin_jobs_client.get(f"/admin/jobs/fix_nested_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # success count
    assert "Template:Test1" in page
    assert "Template:Test2" in page
    assert "Template:Test3" in page


def test_fix_nested_job_detail_page_handles_nonexistent_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test that the fix nested job detail page handles nonexistent job gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    response = admin_jobs_client.get("/admin/jobs/fix_nested_main_files/999", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Job id 999 was not found", "warning")


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin_routes.jobs.load_auth_payload")
def test_start_fix_nested_main_files_job_route(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that the start fix nested main files job route works."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.return_value = 1

    response = admin_jobs_client.post("/admin/jobs/fix_nested_main_files/start")
    assert response.status_code == 302
    mock_flash.assert_any_call("Job 1 started to fix_nested_main_files.", "success")

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_fix_nested_jobs_page_has_start_button(admin_jobs_client, jobs_db):
    """Test that the fix nested jobs page has a start button."""

    response = admin_jobs_client.get("/admin/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'type="submit"' in page
    assert 'action="/admin/jobs/fix_nested_main_files/start"' in page


def test_fix_nested_jobs_list_filters_by_job_type(admin_jobs_client, jobs_db):
    """Test that the fix nested jobs list only shows fix_nested_main_files jobs."""

    # Create jobs of different types (complete first before creating second of same type)
    job1 = jobs_db.create("fix_nested_main_files")
    jobs_db.update_status(job1.id, "completed", job_type="fix_nested_main_files")
    jobs_db.create("fix_nested_main_files")
    jobs_db.create("collect_templates_data")
    jobs_db.create("other_job_type")

    response = admin_jobs_client.get("/admin/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 4)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_fix_nested_job_detail_page_redirects_for_wrong_job_type(admin_jobs_client, jobs_db, monkeypatch):
    """Test that accessing a non-fix_nested job via fix_nested route redirects."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a collect_templates_data job
    job = jobs_db.create("collect_templates_data")

    response = admin_jobs_client.get(f"/admin/jobs/fix_nested_main_files/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job id {job.id} was not found", "warning")


def test_job_detail_rejects_wrong_job_type(admin_jobs_client, jobs_db, monkeypatch):
    """Test that accessing detail page of non-collect_templates_data job is rejected."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    job = jobs_db.create("other_job_type")

    response = admin_jobs_client.get(f"/admin/jobs/collect_templates_data/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job id {job.id} was not found", "warning")


def test_delete_collect_templates_data_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test deleting a collect_templates_data job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a job
    job = jobs_db.create("collect_templates_data")
    assert len(jobs_db.list()) == 1

    # Delete the job
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(f"/admin/jobs/collect_templates_data/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} deleted successfully.", "success")

    # Verify job is deleted
    assert len(jobs_db.list()) == 0


def test_delete_fix_nested_main_files_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test deleting a fix_nested_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a job
    job = jobs_db.create("fix_nested_main_files")
    assert len(jobs_db.list()) == 1

    # Delete the job
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(f"/admin/jobs/fix_nested_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} deleted successfully.", "success")

    # Verify job is deleted
    assert len(jobs_db.list()) == 0


def test_delete_nonexistent_job(monkeypatch, admin_jobs_client):
    """Test deleting a non-existent job shows appropriate error."""
    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Try to delete a job that doesn't exist
    response = admin_jobs_client.post("/admin/jobs/collect_templates_data/999/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_with("Failed to delete job 999", "danger")


def test_delete_job_with_wrong_type(admin_jobs_client, jobs_db):
    """Test deleting a job through the wrong job type endpoint."""

    # Create a collect_templates_data job
    job = jobs_db.create("collect_templates_data")

    # Try to delete it via the fix_nested endpoint
    response = admin_jobs_client.post(f"/admin/jobs/fix_nested_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200

    # The job should still exist (delete should fail)
    remaining_jobs = jobs_db.list()
    assert len(remaining_jobs) == 1


def test_delete_multiple_jobs(admin_jobs_client, jobs_db):
    """Test deleting multiple jobs one by one."""

    # Create multiple jobs (complete first before creating second of same type)
    job1 = jobs_db.create("collect_templates_data")
    jobs_db.update_status(job1.id, "completed", job_type="collect_templates_data")
    job2 = jobs_db.create("collect_templates_data")
    job3 = jobs_db.create("fix_nested_main_files")
    assert len(jobs_db.list()) == 3

    # Delete first collect_templates_data job
    response = admin_jobs_client.post(f"/admin/jobs/collect_templates_data/{job1.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert len(jobs_db.list()) == 2

    # Delete second collect_templates_data job
    response = admin_jobs_client.post(f"/admin/jobs/collect_templates_data/{job2.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert len(jobs_db.list()) == 1

    # Delete fix_nested_main_files job
    response = admin_jobs_client.post(f"/admin/jobs/fix_nested_main_files/{job3.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert len(jobs_db.list()) == 0


def test_cancel_collect_templates_data_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test cancelling a collect_templates_data job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a job
    job = jobs_db.create("collect_templates_data")
    jobs_db.update_status(job.id, "running", job_type="collect_templates_data")

    # Cancel the job
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=True):
        response = admin_jobs_client.post(f"/admin/jobs/collect_templates_data/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} cancellation requested.", "success")


def test_cancel_fix_nested_main_files_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test cancelling a fix_nested_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a job
    job = jobs_db.create("fix_nested_main_files")
    jobs_db.update_status(job.id, "running", job_type="fix_nested_main_files")

    # Cancel the job
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=True):
        response = admin_jobs_client.post(f"/admin/jobs/fix_nested_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} cancellation requested.", "success")


# ================================================================================
# download_main_files tests
# ================================================================================


def test_download_main_files_jobs_list_page_displays_jobs(admin_jobs_client, jobs_db):
    """Test that the download main files jobs list page displays jobs."""

    # Create some test jobs (complete first before creating second of same type)
    job1 = jobs_db.create("download_main_files")
    jobs_db.update_status(job1.id, "completed", job_type="download_main_files")
    jobs_db.create("download_main_files")

    response = admin_jobs_client.get("/admin/jobs/download_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Download Main Files Jobs" in page


def test_download_main_files_jobs_list_page_shows_no_jobs_message(admin_jobs_client, jobs_db):
    """Test that the download main files jobs list page shows a message when there are no jobs."""

    response = admin_jobs_client.get("/admin/jobs/download_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Download Main Files Jobs" in page


def test_download_main_files_job_detail_page_displays_job_info(admin_jobs_client, jobs_db):
    """Test that the download main files job detail page displays job information."""

    job = jobs_db.create("download_main_files")
    jobs_db.update_status(job.id, "completed", job_type="download_main_files")

    response = admin_jobs_client.get(f"/admin/jobs/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Download Main Files Job #{job.id}" in page
    assert "Completed" in page


def test_download_main_files_job_detail_page_shows_result_data(admin_jobs_client, jobs_db, tmp_path):
    """Test that the download main files job detail page displays result data from JSON file."""

    job = jobs_db.create("download_main_files")

    # Create a fake result file
    result_data = {
        "job_id": job.id,
        "output_path": str(tmp_path / "main_files"),
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

    jobs_db.update_status(job.id, "completed", str(result_file), job_type="download_main_files")

    response = admin_jobs_client.get(f"/admin/jobs/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # downloaded count
    assert "test1.svg" in page
    assert "Template:Test2" in page


def test_download_main_files_job_detail_page_handles_nonexistent_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test that the download main files job detail page handles nonexistent job gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    response = admin_jobs_client.get("/admin/jobs/download_main_files/999", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Job id 999 was not found", "warning")


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin_routes.jobs.load_auth_payload")
def test_start_download_main_files_job_route(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that the start download main files job route works."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.return_value = 1

    response = admin_jobs_client.post("/admin/jobs/download_main_files/start")
    assert response.status_code == 302
    mock_flash.assert_any_call("Job 1 started to download_main_files.", "success")

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_download_main_files_jobs_page_has_start_button(admin_jobs_client, jobs_db):
    """Test that the download main files jobs page has a start button."""

    response = admin_jobs_client.get("/admin/jobs/download_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'type="submit"' in page
    assert 'action="/admin/jobs/download_main_files/start"' in page


def test_download_main_files_jobs_list_filters_by_job_type(admin_jobs_client, jobs_db):
    """Test that the download main files jobs list only shows download_main_files jobs."""

    # Create jobs of different types (complete first before creating second of same type)
    job1 = jobs_db.create("download_main_files")
    jobs_db.update_status(job1.id, "completed", job_type="download_main_files")
    jobs_db.create("download_main_files")
    jobs_db.create("collect_templates_data")
    jobs_db.create("fix_nested_main_files")

    response = admin_jobs_client.get("/admin/jobs/download_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 4)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_download_main_files_job_detail_page_redirects_for_wrong_job_type(admin_jobs_client, jobs_db, monkeypatch):
    """Test that accessing a non-download_main_files job via download route redirects."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a collect_templates_data job
    job = jobs_db.create("collect_templates_data")

    response = admin_jobs_client.get(f"/admin/jobs/download_main_files/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job id {job.id} was not found", "warning")


def test_delete_download_main_files_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test deleting a download_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a job
    job = jobs_db.create("download_main_files")
    assert len(jobs_db.list()) == 1

    # Delete the job
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(f"/admin/jobs/download_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} deleted successfully.", "success")

    # Verify job is deleted
    assert len(jobs_db.list()) == 0


def test_cancel_download_main_files_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test cancelling a download_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Create a job
    job = jobs_db.create("download_main_files")
    jobs_db.update_status(job.id, "running", job_type="download_main_files")

    # Cancel the job
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=True):
        response = admin_jobs_client.post(f"/admin/jobs/download_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} cancellation requested.", "success")


def test_cancel_job_not_running(admin_jobs_client, jobs_db, monkeypatch):
    """Test cancelling a job that's not running shows appropriate message."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    job = jobs_db.create("download_main_files")
    jobs_db.update_status(job.id, "completed", job_type="download_main_files")

    # Try to cancel a completed job
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(f"/admin/jobs/download_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} is not running or already cancelled.", "warning")


def test_job_list_page_with_invalid_job_type_returns_404(admin_jobs_client, jobs_db):
    """Test that requesting an invalid job type returns 404."""

    response = admin_jobs_client.get("/admin/jobs/invalid_job_type")
    assert response.status_code == 404


def test_start_job_without_user_login(admin_jobs_client, monkeypatch):
    """Test starting a job without being logged in."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    # Mock current_user to return None
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.load_user", lambda: None)

    response = admin_jobs_client.post("/admin/jobs/collect_templates_data/start", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("You must be logged in to start this job.", "danger")


@patch("src.main_app.jobs_workers.jobs_worker.start_job")
@patch("src.main_app.app_routes.admin_routes.jobs.load_auth_payload")
def test_start_job_handles_exception(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that job start handles exceptions gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.side_effect = Exception("Database error")

    response = admin_jobs_client.post("/admin/jobs/collect_templates_data/start", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Failed to start job. Please try again.", "danger")


def test_delete_job_handles_exception(admin_jobs_client, jobs_db, monkeypatch):
    """Test that job deletion handles exceptions gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    job = jobs_db.create("collect_templates_data")

    # Mock delete to raise an exception
    def mock_delete_job(job_id, job_type):
        raise Exception("Database error")

    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.delete_job", mock_delete_job)

    response = admin_jobs_client.post(f"/admin/jobs/collect_templates_data/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Failed to delete job {job.id}", "danger")


def test_download_main_files_job_with_partial_results(admin_jobs_client, jobs_db, tmp_path):
    """Test displaying partial results for a running job."""

    job = jobs_db.create("download_main_files")

    # Create a result file with partial results
    result_data = {
        "job_id": job.id,
        "output_path": str(tmp_path / "main_files"),
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

    jobs_db.update_status(job.id, "running", str(result_file), job_type="download_main_files")

    response = admin_jobs_client.get(f"/admin/jobs/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "5" in page  # downloaded count
    assert "running" in page.lower()


def test_cancel_already_cancelled_job(admin_jobs_client, jobs_db, monkeypatch):
    """Test cancelling a job that's already been cancelled."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.jobs.flash", mock_flash)

    job = jobs_db.create("download_main_files")
    jobs_db.update_status(job.id, "cancelled", job_type="download_main_files")

    # Try to cancel again
    with patch("src.main_app.app_routes.admin_routes.jobs.jobs_worker.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(f"/admin/jobs/download_main_files/{job.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} is not running or already cancelled.", "warning")
