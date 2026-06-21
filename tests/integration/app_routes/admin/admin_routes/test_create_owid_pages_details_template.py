"""
Integration tests for the create_owid_pages job detail template.

Tests cover the PR changes to:
src/templates/jobs_templates/admin/create_owid_pages/details.html

Changes tested:
- Added 'Update Page' column header
- Template title now strips "Template:OWID/" prefix via Jinja replace filter
- step_keys now includes 'update_text' step
"""

from __future__ import annotations

import json
from html import unescape
from types import SimpleNamespace
from typing import Any, Generator, NoReturn

import pytest
from flask.testing import FlaskClient

from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.db.services import jobs_service as _sqlalchemy_jobs_service
from src.main_app.extensions import db as _db


@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch) -> Generator[FlaskClient, Any, NoReturn]:
    """Flask test client with admin auth mocked out."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    admin_user = SimpleNamespace(username="admin", is_active_admin=True)

    def fake_current_user() -> SimpleNamespace:
        return admin_user

    monkeypatch.setattr("src.main_app.app_routes.auth.utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.admin.decorators.load_user", fake_current_user)
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


def _create_job_with_result(result_data: dict, tmp_path, job_type: str = "create_owid_pages"):
    """Helper to persist a job and a JSON result file, returning the job."""
    job = _sqlalchemy_jobs_service.create_job(job_type, "admin")
    result_file = tmp_path / "result.json"
    result_file.write_text(json.dumps(result_data))
    _sqlalchemy_jobs_service.update_job_status(job.id, "completed", str(result_file), job_type=job_type)
    return job


def _minimal_result_data(pages_created=None, pages_updated=None):
    """Return a minimal result_data dict for the create_owid_pages template."""
    return {
        "summary": {
            "processed": 1,
            "total": 1,
            "created": len(pages_created or []),
            "updated": len(pages_updated or []),
            "skipped": 0,
            "failed": 0,
        },
        "pages_created": pages_created or [],
        "pages_updated": pages_updated or [],
        "pages_skipped": [],
        "pages_failed": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Column headers
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdatePageColumnHeader:
    def test_update_page_column_header_is_present(self, admin_jobs_client, tmp_path):
        """The 'Update Page' column header added in this PR is rendered in the table."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/some-chart",
                    "new_page_title": "Commons:OWID/some-chart",
                    "status": "created",
                    "steps": {
                        "load_template_text": {"result": True, "msg": "loaded"},
                        "create_new_text": {"result": True, "msg": "created"},
                        "update_text": {"result": True, "msg": "updated"},
                        "create_new_page": {"result": True, "msg": "page created"},
                    },
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Update Page" in page

    def test_update_page_column_appears_before_create_page_column(self, admin_jobs_client, tmp_path):
        """'Update Page' column appears before 'Create Page' in the header row."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/test",
                    "new_page_title": None,
                    "status": "created",
                    "steps": None,
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        update_pos = page.find("Update Page")
        create_pos = page.find("Create Page")
        assert update_pos != -1, "'Update Page' header not found"
        assert create_pos != -1, "'Create Page' header not found"
        assert update_pos < create_pos, "'Update Page' should appear before 'Create Page'"


# ─────────────────────────────────────────────────────────────────────────────
# Template title filter: replace("Template:OWID/", "", 1)
# ─────────────────────────────────────────────────────────────────────────────


class TestTemplateTitleFilter:
    def test_template_owid_prefix_is_stripped(self, admin_jobs_client, tmp_path):
        """'Template:OWID/' prefix is removed from the displayed link text."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/health-expenditure",
                    "new_page_title": None,
                    "status": "created",
                    "steps": None,
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        # The stripped version should appear as link text
        assert "health-expenditure" in page
        # The full prefix should only appear in the href, not as visible text
        # Verify the stripped text is present (the replace filter worked)
        assert "Template:OWID/health-expenditure" in page  # in href
        # Check that the visible text (not in href) is stripped
        # The link text is between > and </a>
        import re

        link_texts = re.findall(r'rel="noopener noreferrer">\s*(.*?)\s*</a>', page, re.DOTALL)
        template_links = [t.strip() for t in link_texts if "health-expenditure" in t]
        assert any(
            t == "health-expenditure" for t in template_links
        ), f"Expected stripped title as link text, got: {template_links}"

    def test_prefix_only_stripped_once(self, admin_jobs_client, tmp_path):
        """The replace filter with count=1 strips only the first occurrence of the prefix."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/Template:OWID/double-prefix",
                    "new_page_title": None,
                    "status": "created",
                    "steps": None,
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        import re

        link_texts = re.findall(r'rel="noopener noreferrer">\s*(.*?)\s*</a>', page, re.DOTALL)
        template_links = [t.strip() for t in link_texts if "double-prefix" in t]
        # Only one prefix should be stripped; remaining text starts with "Template:OWID/"
        assert any(
            "Template:OWID/double-prefix" in t for t in template_links
        ), f"Expected only one prefix stripped, got: {template_links}"

    def test_title_without_owid_prefix_unchanged(self, admin_jobs_client, tmp_path):
        """Titles without 'Template:OWID/' prefix are displayed unchanged."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:SomeOtherTemplate",
                    "new_page_title": None,
                    "status": "created",
                    "steps": None,
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        import re

        link_texts = re.findall(r'rel="noopener noreferrer">\s*(.*?)\s*</a>', page, re.DOTALL)
        template_links = [t.strip() for t in link_texts if "SomeOtherTemplate" in t]
        assert any(
            "Template:SomeOtherTemplate" in t for t in template_links
        ), f"Expected full title unchanged, got: {template_links}"


# ─────────────────────────────────────────────────────────────────────────────
# update_text step rendering
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateTextStep:
    def test_update_text_step_success_renders_badge(self, admin_jobs_client, tmp_path):
        """A successful 'update_text' step is rendered with the success badge."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/chart-a",
                    "new_page_title": "Commons:OWID/chart-a",
                    "status": "created",
                    "steps": {
                        "load_template_text": {"result": True, "msg": ""},
                        "create_new_text": {"result": True, "msg": ""},
                        "update_text": {"result": True, "msg": "text updated"},
                        "create_new_page": {"result": True, "msg": ""},
                    },
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        # render_step renders a success badge with bg-success class
        assert "bg-success" in page

    def test_update_text_step_failure_renders_danger_badge(self, admin_jobs_client, tmp_path):
        """A failed 'update_text' step renders a danger badge."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/chart-b",
                    "new_page_title": None,
                    "status": "created",
                    "steps": {
                        "load_template_text": {"result": True, "msg": ""},
                        "create_new_text": {"result": True, "msg": ""},
                        "update_text": {"result": False, "msg": "update failed"},
                        "create_new_page": {"result": None, "msg": "skipped"},
                    },
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "bg-danger" in page

    def test_missing_update_text_step_renders_dash(self, admin_jobs_client, tmp_path):
        """When 'update_text' key is absent from steps, a dash placeholder is rendered."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/chart-c",
                    "new_page_title": None,
                    "status": "created",
                    "steps": {
                        "load_template_text": {"result": True, "msg": ""},
                        "create_new_text": {"result": True, "msg": ""},
                        # update_text key intentionally absent
                        "create_new_page": {"result": True, "msg": ""},
                    },
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        # render_step with None renders text-muted dash
        assert "text-muted" in page

    def test_four_step_columns_rendered(self, admin_jobs_client, tmp_path):
        """All four step columns (Load Text, Generate Text, Update Page, Create Page) are rendered."""
        result_data = _minimal_result_data(
            pages_created=[
                {
                    "template_title": "Template:OWID/chart-d",
                    "new_page_title": None,
                    "status": "created",
                    "steps": {
                        "load_template_text": {"result": True, "msg": ""},
                        "create_new_text": {"result": True, "msg": ""},
                        "update_text": {"result": True, "msg": ""},
                        "create_new_page": {"result": True, "msg": ""},
                    },
                }
            ]
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/create_owid_pages/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Load Text" in page
        assert "Generate Text" in page
        assert "Update Page" in page
        assert "Create Page" in page
