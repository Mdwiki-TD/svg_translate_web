"""Integration tests for the admin jobs management routes."""

from __future__ import annotations

import json
from html import unescape
from unittest.mock import Mock, patch


def test_jobs_list_page_displays_jobs(admin_jobs_client, mock_jobs_db):
    """Test that the jobs list page displays jobs."""

    # Create some test jobs (complete first before creating second of same type)
    job1 = mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.update_status(job1.id, "completed", job_type="collect_templates_data")
    mock_jobs_db.create("collect_templates_data")

    response = admin_jobs_client.get("/adminpanel/jobs/collect_templates_data")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Collect Templates data Jobs" in page


def test_jobs_list_page_shows_no_jobs_message(admin_jobs_client, mock_jobs_db):
    """Test that the jobs list page shows a message when there are no jobs."""

    response = admin_jobs_client.get("/adminpanel/jobs/collect_templates_data")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Collect Templates data Jobs" in page


def test_job_detail_page_displays_job_info(admin_jobs_client, mock_jobs_db):
    """Test that the job detail page displays job information."""

    job = mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.update_status(job.id, "completed", job_type="collect_templates_data")

    response = admin_jobs_client.get(f"/adminpanel/jobs/collect_templates_data/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Collect Templates data Job #{job.id}" in page
    assert "Completed" in page


def test_job_detail_page_shows_result_data(admin_jobs_client, mock_jobs_db, tmp_path):
    """Test that the job detail page displays result data from JSON file."""

    job = mock_jobs_db.create("collect_templates_data")

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

    mock_jobs_db.update_status(job.id, "completed", str(result_file), job_type="collect_templates_data")

    response = admin_jobs_client.get(f"/adminpanel/jobs/collect_templates_data/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # updated count
    assert "Template:Test1" in page
    assert "Template:Test2" in page


def test_job_detail_page_handles_nonexistent_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test that the job detail page handles nonexistent job gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    response = admin_jobs_client.get("/adminpanel/jobs/collect_templates_data/999", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Job id 999 was not found", "warning")


@patch("src.main_app.public.jobs_routes_utils.start_job")
@patch("src.main_app.public.jobs_routes_utils.load_auth_payload")
def test_start_collect_templates_data_job_route(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that the start collect templates data job route works."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    # Mock the job creation
    mock_start_job.return_value = 1

    response = admin_jobs_client.post("/adminpanel/jobs/collect_templates_data/start")
    assert response.status_code == 302
    mock_flash.assert_any_call("Job 1 started to collect_templates_data.", "success")

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_jobs_page_has_collect_button(admin_jobs_client, mock_jobs_db):
    """Test that the jobs page has a collect templates data button."""

    response = admin_jobs_client.get("/adminpanel/jobs/collect_templates_data")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'action="/adminpanel/jobs/collect_templates_data/start"' in page
    assert 'type="submit"' in page


def test_jobs_list_filters_by_job_type(admin_jobs_client, mock_jobs_db):
    """Test that the jobs list only shows collect_templates_data jobs."""

    # Create jobs of different types
    job1 = mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.update_status(job1.id, "completed", job_type="collect_templates_data")
    mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.create("other_job_type")

    response = admin_jobs_client.get("/adminpanel/jobs/collect_templates_data")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 3)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_fix_nested_jobs_list_page_displays_jobs(admin_jobs_client, mock_jobs_db):
    """Test that the fix nested jobs list page displays jobs."""

    # Create some test jobs (complete first before creating second of same type)
    job1 = mock_jobs_db.create("fix_nested_main_files")
    mock_jobs_db.update_status(job1.id, "completed", job_type="fix_nested_main_files")
    mock_jobs_db.create("fix_nested_main_files")

    response = admin_jobs_client.get("/adminpanel/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Fix Nested Main Files Jobs" in page


def test_fix_nested_jobs_list_page_shows_no_jobs_message(admin_jobs_client, mock_jobs_db):
    """Test that the fix nested jobs list page shows a message when there are no jobs."""

    response = admin_jobs_client.get("/adminpanel/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Fix Nested Main Files Jobs" in page


def test_fix_nested_job_detail_page_displays_job_info(admin_jobs_client, mock_jobs_db):
    """Test that the fix nested job detail page displays job information."""

    job = mock_jobs_db.create("fix_nested_main_files")
    mock_jobs_db.update_status(job.id, "completed", job_type="fix_nested_main_files")

    response = admin_jobs_client.get(f"/adminpanel/jobs/fix_nested_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Fix Nested Main Files Job #{job.id}" in page
    assert "Completed" in page


def test_fix_nested_job_detail_page_shows_result_data(admin_jobs_client, mock_jobs_db, tmp_path):
    """Test that the fix nested job detail page displays result data from JSON file."""

    job = mock_jobs_db.create("fix_nested_main_files")

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
            {"id": 1, "title": "Template:Test1", "main_file": "test1.svg", "fix_result": {"message": "success"}},
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

    mock_jobs_db.update_status(job.id, "completed", str(result_file), job_type="fix_nested_main_files")

    response = admin_jobs_client.get(f"/adminpanel/jobs/fix_nested_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # success count
    assert "Template:Test1" in page
    assert "Template:Test2" in page
    assert "Template:Test3" in page


def test_fix_nested_job_detail_page_handles_nonexistent_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test that the fix nested job detail page handles nonexistent job gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    response = admin_jobs_client.get("/adminpanel/jobs/fix_nested_main_files/999", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Job id 999 was not found", "warning")


@patch("src.main_app.public.jobs_routes_utils.start_job")
@patch("src.main_app.public.jobs_routes_utils.load_auth_payload")
def test_start_fix_nested_main_files_job_route(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that the start fix nested main files job route works."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.return_value = 1

    response = admin_jobs_client.post("/adminpanel/jobs/fix_nested_main_files/start")
    assert response.status_code == 302
    mock_flash.assert_any_call("Job 1 started to fix_nested_main_files.", "success")

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_fix_nested_jobs_page_has_start_button(admin_jobs_client, mock_jobs_db):
    """Test that the fix nested jobs page has a start button."""

    response = admin_jobs_client.get("/adminpanel/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'type="submit"' in page
    assert 'action="/adminpanel/jobs/fix_nested_main_files/start"' in page


def test_fix_nested_jobs_list_filters_by_job_type(admin_jobs_client, mock_jobs_db):
    """Test that the fix nested jobs list only shows fix_nested_main_files jobs."""

    # Create jobs of different types (complete first before creating second of same type)
    job1 = mock_jobs_db.create("fix_nested_main_files")
    mock_jobs_db.update_status(job1.id, "completed", job_type="fix_nested_main_files")
    mock_jobs_db.create("fix_nested_main_files")
    mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.create("other_job_type")

    response = admin_jobs_client.get("/adminpanel/jobs/fix_nested_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 4)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_fix_nested_job_detail_page_redirects_for_wrong_job_type(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test that accessing a non-fix_nested job via fix_nested route redirects."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a collect_templates_data job
    job = mock_jobs_db.create("collect_templates_data")

    response = admin_jobs_client.get(f"/adminpanel/jobs/fix_nested_main_files/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job id {job.id} was not found", "warning")


def test_job_detail_rejects_wrong_job_type(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test that accessing detail page of non-collect_templates_data job is rejected."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    job = mock_jobs_db.create("other_job_type")

    response = admin_jobs_client.get(f"/adminpanel/jobs/collect_templates_data/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job id {job.id} was not found", "warning")


def test_delete_collect_templates_data_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test deleting a collect_templates_data job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a job
    job = mock_jobs_db.create("collect_templates_data")
    assert len(mock_jobs_db.list()) == 1

    # Delete the job
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/collect_templates_data/{job.id}/delete", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} deleted successfully.", "success")

    # Verify job is deleted
    assert len(mock_jobs_db.list()) == 0


def test_delete_fix_nested_main_files_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test deleting a fix_nested_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a job
    job = mock_jobs_db.create("fix_nested_main_files")
    assert len(mock_jobs_db.list()) == 1

    # Delete the job
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/fix_nested_main_files/{job.id}/delete", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} deleted successfully.", "success")

    # Verify job is deleted
    assert len(mock_jobs_db.list()) == 0


def test_delete_nonexistent_job(monkeypatch, admin_jobs_client):
    """Test deleting a non-existent job shows appropriate error."""
    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Try to delete a job that doesn't exist
    response = admin_jobs_client.post("/adminpanel/jobs/collect_templates_data/999/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_with("Job not found.", "warning")


def test_delete_job_with_wrong_type(admin_jobs_client, mock_jobs_db):
    """Test deleting a job through the wrong job type endpoint."""

    # Create a collect_templates_data job
    job = mock_jobs_db.create("collect_templates_data")

    # Try to delete it via the fix_nested endpoint
    response = admin_jobs_client.post(f"/adminpanel/jobs/fix_nested_main_files/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200

    # The job should still exist (delete should fail)
    remaining_jobs = mock_jobs_db.list()
    assert len(remaining_jobs) == 1


def test_delete_multiple_jobs(admin_jobs_client, mock_jobs_db):
    """Test deleting multiple jobs one by one."""

    # Create multiple jobs (complete first before creating second of same type)
    job1 = mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.update_status(job1.id, "completed", job_type="collect_templates_data")
    job2 = mock_jobs_db.create("collect_templates_data")
    job3 = mock_jobs_db.create("fix_nested_main_files")
    assert len(mock_jobs_db.list()) == 3

    # Delete first collect_templates_data job
    response = admin_jobs_client.post(
        f"/adminpanel/jobs/collect_templates_data/{job1.id}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert len(mock_jobs_db.list()) == 2

    # Delete second collect_templates_data job
    response = admin_jobs_client.post(
        f"/adminpanel/jobs/collect_templates_data/{job2.id}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert len(mock_jobs_db.list()) == 1

    # Delete fix_nested_main_files job
    response = admin_jobs_client.post(f"/adminpanel/jobs/fix_nested_main_files/{job3.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert len(mock_jobs_db.list()) == 0


def test_cancel_collect_templates_data_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test cancelling a collect_templates_data job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a job
    job = mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.update_status(job.id, "running", job_type="collect_templates_data")

    # Cancel the job
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=True):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/collect_templates_data/{job.id}/cancel", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} cancellation requested.", "success")


def test_cancel_fix_nested_main_files_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test cancelling a fix_nested_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a job
    job = mock_jobs_db.create("fix_nested_main_files")
    mock_jobs_db.update_status(job.id, "running", job_type="fix_nested_main_files")

    # Cancel the job
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=True):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/fix_nested_main_files/{job.id}/cancel", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} cancellation requested.", "success")


# ================================================================================
# download_main_files tests
# ================================================================================


def test_download_main_files_jobs_list_page_displays_jobs(admin_jobs_client, mock_jobs_db):
    """Test that the download main files jobs list page displays jobs."""

    # Create some test jobs (complete first before creating second of same type)
    job1 = mock_jobs_db.create("download_main_files")
    mock_jobs_db.update_status(job1.id, "completed", job_type="download_main_files")
    mock_jobs_db.create("download_main_files")

    response = admin_jobs_client.get("/adminpanel/jobs/download_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Download Main Files Jobs" in page


def test_download_main_files_jobs_list_page_shows_no_jobs_message(admin_jobs_client, mock_jobs_db):
    """Test that the download main files jobs list page shows a message when there are no jobs."""

    response = admin_jobs_client.get("/adminpanel/jobs/download_main_files")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Download Main Files Jobs" in page


def test_download_main_files_job_detail_page_displays_job_info(admin_jobs_client, mock_jobs_db):
    """Test that the download main files job detail page displays job information."""

    job = mock_jobs_db.create("download_main_files")
    mock_jobs_db.update_status(job.id, "completed", job_type="download_main_files")

    response = admin_jobs_client.get(f"/adminpanel/jobs/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert f"Download Main Files Job #{job.id}" in page
    assert "Completed" in page


def test_download_main_files_job_detail_page_shows_result_data(admin_jobs_client, mock_jobs_db, tmp_path):
    """Test that the download main files job detail page displays result data from JSON file."""

    job = mock_jobs_db.create("download_main_files")

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

    mock_jobs_db.update_status(job.id, "completed", str(result_file), job_type="download_main_files")

    response = admin_jobs_client.get(f"/adminpanel/jobs/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Job Summary" in page
    assert "3" in page  # downloaded count
    assert "test1.svg" in page
    assert "Template:Test2" in page


def test_download_main_files_job_detail_page_handles_nonexistent_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test that the download main files job detail page handles nonexistent job gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    response = admin_jobs_client.get("/adminpanel/jobs/download_main_files/999", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Job id 999 was not found", "warning")


@patch("src.main_app.public.jobs_routes_utils.start_job")
@patch("src.main_app.public.jobs_routes_utils.load_auth_payload")
def test_start_download_main_files_job_route(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that the start download main files job route works."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Mock the auth payload and job creation
    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.return_value = 1

    response = admin_jobs_client.post("/adminpanel/jobs/download_main_files/start")
    assert response.status_code == 302
    mock_flash.assert_any_call("Job 1 started to download_main_files.", "success")

    mock_start_job.assert_called_once()
    mock_load_auth.assert_called_once()


def test_download_main_files_jobs_page_has_start_button(admin_jobs_client, mock_jobs_db):
    """Test that the download main files jobs page has a start button."""

    response = admin_jobs_client.get("/adminpanel/jobs/download_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'type="submit"' in page
    assert 'action="/adminpanel/jobs/download_main_files/start"' in page


def test_download_main_files_jobs_list_filters_by_job_type(admin_jobs_client, mock_jobs_db):
    """Test that the download main files jobs list only shows download_main_files jobs."""

    # Create jobs of different types (complete first before creating second of same type)
    job1 = mock_jobs_db.create("download_main_files")
    mock_jobs_db.update_status(job1.id, "completed", job_type="download_main_files")
    mock_jobs_db.create("download_main_files")
    mock_jobs_db.create("collect_templates_data")
    mock_jobs_db.create("fix_nested_main_files")

    response = admin_jobs_client.get("/adminpanel/jobs/download_main_files")
    assert response.status_code == 200
    page = response.get_data(as_text=True)

    # Should show 2 rows of jobs (not 4)
    # Count the number of "View" buttons which appear once per job row
    assert page.count("btn btn-outline-primary btn-sm") == 2


def test_download_main_files_job_detail_page_redirects_for_wrong_job_type(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test that accessing a non-download_main_files job via download route redirects."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a collect_templates_data job
    job = mock_jobs_db.create("collect_templates_data")

    response = admin_jobs_client.get(f"/adminpanel/jobs/download_main_files/{job.id}", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job id {job.id} was not found", "warning")


def test_delete_download_main_files_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test deleting a download_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a job
    job = mock_jobs_db.create("download_main_files")
    assert len(mock_jobs_db.list()) == 1

    # Delete the job
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/download_main_files/{job.id}/delete", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} deleted successfully.", "success")

    # Verify job is deleted
    assert len(mock_jobs_db.list()) == 0


def test_cancel_download_main_files_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test cancelling a download_main_files job."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Create a job
    job = mock_jobs_db.create("download_main_files")
    mock_jobs_db.update_status(job.id, "running", job_type="download_main_files")

    # Cancel the job
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=True):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/download_main_files/{job.id}/cancel", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} cancellation requested.", "success")


def test_cancel_job_not_running(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test cancelling a job that's not running shows appropriate message."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    job = mock_jobs_db.create("download_main_files")
    mock_jobs_db.update_status(job.id, "completed", job_type="download_main_files")

    # Try to cancel a completed job
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/download_main_files/{job.id}/cancel", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} is not running or already cancelled.", "warning")


def test_job_list_page_with_invalid_job_type_returns_404(admin_jobs_client, mock_jobs_db):
    """Test that requesting an invalid job type returns 404."""

    response = admin_jobs_client.get("/adminpanel/jobs/invalid_job_type")
    assert response.status_code == 404


def test_start_job_without_user_login(admin_jobs_client, monkeypatch):
    """Test starting a job without being logged in."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    # Mock current_user to return None
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: None)

    response = admin_jobs_client.post("/adminpanel/jobs/collect_templates_data/start", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("You must be logged in to start this job.", "danger")


@patch("src.main_app.public.jobs_routes_utils.start_job")
@patch("src.main_app.public.jobs_routes_utils.load_auth_payload")
def test_start_job_handles_exception(mock_load_auth, mock_start_job, admin_jobs_client, monkeypatch):
    """Test that job start handles exceptions gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    mock_load_auth.return_value = {"username": "admin"}
    mock_start_job.side_effect = Exception("Database error")

    response = admin_jobs_client.post("/adminpanel/jobs/collect_templates_data/start", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Failed to start job. Please try again.", "danger")


def test_delete_job_handles_exception(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test that job deletion handles exceptions gracefully."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    job = mock_jobs_db.create("collect_templates_data")

    # Mock delete to raise an exception
    def mock_delete_job(job_id, job_type):
        raise Exception("Database error")

    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.JobsService.delete", mock_delete_job)

    response = admin_jobs_client.post(f"/adminpanel/jobs/collect_templates_data/{job.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Failed to delete job {job.id}", "danger")


def test_download_main_files_job_with_partial_results(admin_jobs_client, mock_jobs_db, tmp_path):
    """Test displaying partial results for a running job."""

    job = mock_jobs_db.create("download_main_files")

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

    mock_jobs_db.update_status(job.id, "running", str(result_file), job_type="download_main_files")

    response = admin_jobs_client.get(f"/adminpanel/jobs/download_main_files/{job.id}")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "5" in page  # downloaded count
    assert "running" in page.lower()


def test_cancel_already_cancelled_job(admin_jobs_client, mock_jobs_db, monkeypatch):
    """Test cancelling a job that's already been cancelled."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", mock_flash)

    job = mock_jobs_db.create("download_main_files")
    mock_jobs_db.update_status(job.id, "cancelled", job_type="download_main_files")

    # Try to cancel again
    with patch("src.main_app.public.jobs_routes_utils.cancel_job_worker", return_value=False):
        response = admin_jobs_client.post(
            f"/adminpanel/jobs/download_main_files/{job.id}/cancel", follow_redirects=True
        )
    assert response.status_code == 200
    mock_flash.assert_called_once_with(f"Job {job.id} is not running or already cancelled.", "warning")
