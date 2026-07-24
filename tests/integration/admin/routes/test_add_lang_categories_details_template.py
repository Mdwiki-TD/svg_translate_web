"""
Integration tests for the add_lang_categories_to_owid_pages job detail template.

Tests cover:
src/templates/jobs_templates/admin_templates/add_lang_categories_to_owid_pages/details.html
"""

from __future__ import annotations

import json
from html import unescape

from src.main_app.db.services import JobsService, jobs_service as _sqlalchemy_jobs_service


def _create_job_with_result(result_data: dict, tmp_path, job_type: str = "add_lang_categories_to_owid_pages"):
    """Helper to persist a job and a JSON result file, returning the job."""
    job = JobsService().create_job(job_type, "admin")
    result_file = tmp_path / "result.json"
    result_file.write_text(json.dumps(result_data))
    JobsService().update_job_status(job.id, "completed", str(result_file), job_type=job_type)
    return job


def _minimal_result_data(pages_success=None, pages_skipped=None, pages_failed=None):
    """Return a minimal result_data dict for the add_lang_categories_to_owid_pages template."""
    return {
        "summary": {
            "processed": 1,
            "total": 1,
            "success": len(pages_success or []),
            "skipped": len(pages_skipped or []),
            "failed": len(pages_failed or []),
            "no_file": 0,
        },
        "pages_success": pages_success or [],
        "pages_skipped": pages_skipped or [],
        "pages_failed": pages_failed or [],
    }


class TestAddLangCategoriesDetailsTemplate:
    def test_step_columns_rendered(self, admin_jobs_client, tmp_path):
        """All step columns (Load Text, Extract SVG, Get Langs, Build Cats, Check Exist, Save Page) are rendered."""
        result_data = _minimal_result_data(
            pages_success=[
                {
                    "page_title": "OWID/test-page",
                    "svg_file": "test-file.svg",
                    "lang_codes": ["en", "fr"],
                    "categories_added": ["[[Category:English-language SVG]]", "[[Category:French-language SVG]]"],
                    "status": "completed",
                    "steps": {
                        "load_page_text": {"result": True, "msg": "Loaded page text"},
                        "extract_file_name": {"result": True, "msg": "SVG file: test-file.svg"},
                        "get_languages": {"result": True, "msg": "Found 2 languages"},
                        "build_categories": {"result": True, "msg": "Built candidate category names"},
                        "check_existing": {"result": True, "msg": "New category lines to add"},
                        "save_page": {"result": True, "msg": "Saved page"},
                    },
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/adminpanel/jobs/add_lang_categories_to_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))

        # Verify headers exist
        assert "Load Text" in page
        assert "Extract SVG" in page
        assert "Get Langs" in page
        assert "Build Cats" in page
        assert "Check Exist" in page
        assert "Save Page" in page

        # Verify rendered status using render_step (contains check-lg or diff etc)
        assert "bi-check-lg" in page or "bg-success" in page
