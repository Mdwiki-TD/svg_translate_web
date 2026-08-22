"""Integration tests for the crop_main_files job detail template."""

from __future__ import annotations

import json
from html import unescape
from typing import Any

from src.main_app.database.services import JobsService

_JOB_TYPE = "crop_main_files"


def _step(result: bool | None, msg: str) -> dict[str, bool | None | str]:
    """Create a serialized crop-job step result."""
    return {"result": result, "msg": msg}


def _cropped_file_result() -> dict[str, Any]:
    """Create one uploaded cropped-file result with its final update step."""
    return {
        "template_title": "Template:OWID/Wheat production",
        "original_file": "wheat production, World, 2023.svg",
        "cropped_filename": "wheat production, World, 2023 (cropped).svg",
        "status": "uploaded",
        "steps": {
            "download": _step(True, "Downloaded"),
            "crop": _step(True, "Cropped"),
            "upload_cropped": _step(True, "Uploaded"),
            "update_original": _step(None, "No update needed"),
            "update_template": _step(None, "No update needed"),
            "update_page": _step(None, "No update needed"),
            "update_cropped": _step(True, "Updated cropped file wikitext"),
        },
    }


def _result_data() -> dict[str, Any]:
    """Create a minimal serialized crop-job result for the details route."""
    return {
        "summary": {"total": 1, "processed": 1, "uploaded": 1, "updated": 0, "skipped": 0, "failed": 0},
        "pages_uploaded": [_cropped_file_result()],
        "pages_updated": [],
        "pages_skipped": [],
        "pages_failed": [],
        "files_processed": [],
    }


def _create_job_with_result(result_data: dict, tmp_path):
    """Create a completed crop job that points to a serialized result file."""
    job = JobsService().create_job(_JOB_TYPE, "admin")
    result_file = tmp_path / "crop_main_files_result.json"
    result_file.write_text(json.dumps(result_data))
    JobsService().update_job_status(job.id, "completed", str(result_file), job_type=_JOB_TYPE)
    return job


def test_details_page_renders_cropped_file_update_as_final_step(admin_jobs_client, tmp_path):
    """The details table shows the cropped-file update column and saved-page result."""
    job = _create_job_with_result(_result_data(), tmp_path)

    response = admin_jobs_client.get(f"/adminpanel/jobs/{_JOB_TYPE}/{job.id}")

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Update Cropped" in page
    # assert "Updated cropped file wikitext" in page
