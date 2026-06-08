"""
Integration tests for the update_owid_charts job detail template.

Tests cover the PR changes to:
src/templates/jobs_templates/admin/update_owid_charts/details.html

Changes tested:
- Updated charts: when > 100 items and expand_all=False, renders collapsed header
- Updated charts: when > 100 items and expand_all=True, renders full table
- Updated charts: when <= 100 items, always renders full table
- Same three-way logic applied to failed_charts and skipped_charts
"""

from __future__ import annotations

import json
from html import unescape
from types import SimpleNamespace

import pytest

from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.db.services import jobs_service as _sqlalchemy_jobs_service
from src.main_app.extensions import db as _db

_JOB_TYPE = "update_owid_charts"


@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch):
    """Flask test client with admin auth mocked out."""
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


def _make_chart(slug: str = "test-chart") -> dict:
    return {
        "slug": slug,
        "status": "updated",
        "new_min_time": 2000,
        "new_max_time": 2022,
        "new_len_years": 23,
        "owid_variable_id": 12345,
    }


def _make_failed_chart(slug: str = "failed-chart") -> dict:
    return {"slug": slug, "status": "failed", "error": "fetch error"}


def _make_skipped_chart(slug: str = "skipped-chart") -> dict:
    return {"slug": slug, "status": "skipped", "skip_reason": "unchanged"}


def _result_data(updated=None, failed=None, skipped=None) -> dict:
    updated = updated or []
    failed = failed or []
    skipped = skipped or []
    return {
        "summary": {
            "processed": len(updated) + len(failed) + len(skipped),
            "total": len(updated) + len(failed) + len(skipped),
            "updated": len(updated),
            "failed": len(failed),
            "skipped": len(skipped),
        },
        "updated_charts": updated,
        "failed_charts": failed,
        "skipped_charts": skipped,
    }


def _create_job_with_result(result_data: dict, tmp_path):
    job = _sqlalchemy_jobs_service.create_job(_JOB_TYPE, "admin")
    result_file = tmp_path / "result.json"
    result_file.write_text(json.dumps(result_data))
    _sqlalchemy_jobs_service.update_job_status(job.id, "completed", str(result_file), job_type=_JOB_TYPE)
    return job


# ─────────────────────────────────────────────────────────────────────────────
# Updated charts section
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdatedChartsSection:
    def test_small_list_renders_full_table(self, admin_jobs_client, tmp_path):
        """With <= 100 updated charts, the full table is rendered (not a collapsed header)."""
        charts = [_make_chart(f"chart-{i}") for i in range(5)]
        job = _create_job_with_result(_result_data(updated=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Updated Charts (5)" in page
        assert "chart-0" in page  # full table includes row data

    def test_exactly_100_updated_charts_renders_full_table(self, admin_jobs_client, tmp_path):
        """Boundary: exactly 100 updated charts still renders the full table."""
        charts = [_make_chart(f"chart-{i}") for i in range(100)]
        job = _create_job_with_result(_result_data(updated=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Updated Charts (100)" in page
        assert "chart-0" in page

    def test_over_100_updated_charts_collapses_without_expand(self, admin_jobs_client, tmp_path):
        """With > 100 updated charts and no expand_all flag, only the collapsed header is shown."""
        charts = [_make_chart(f"chart-{i}") for i in range(101)]
        job = _create_job_with_result(_result_data(updated=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        # Collapsed header shows count
        assert "Updated Charts (101)" in page
        # The individual chart slugs are not rendered in collapsed mode
        assert "chart-0" not in page

    def test_over_100_updated_charts_renders_full_table_with_expand(self, admin_jobs_client, tmp_path):
        """With > 100 updated charts and expand_all=True, the full table is rendered."""
        charts = [_make_chart(f"chart-{i}") for i in range(101)]
        job = _create_job_with_result(_result_data(updated=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}/expand")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Updated Charts (101)" in page
        assert "chart-0" in page  # full table includes row data

    def test_no_updated_charts_section_absent(self, admin_jobs_client, tmp_path):
        """When there are no updated charts, the Updated Charts section is not rendered."""
        job = _create_job_with_result(_result_data(updated=[]), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Updated Charts" not in page


# ─────────────────────────────────────────────────────────────────────────────
# Failed charts section
# ─────────────────────────────────────────────────────────────────────────────


class TestFailedChartsSection:
    def test_small_list_renders_full_table(self, admin_jobs_client, tmp_path):
        """With <= 100 failed charts, the full table is rendered."""
        charts = [_make_failed_chart(f"chart-{i}") for i in range(3)]
        job = _create_job_with_result(_result_data(failed=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Failed Charts (3)" in page
        assert "chart-0" in page

    def test_exactly_100_failed_charts_renders_full_table(self, admin_jobs_client, tmp_path):
        """Boundary: exactly 100 failed charts renders the full table."""
        charts = [_make_failed_chart(f"chart-{i}") for i in range(100)]
        job = _create_job_with_result(_result_data(failed=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Failed Charts (100)" in page
        assert "chart-0" in page

    def test_over_100_failed_charts_collapses_without_expand(self, admin_jobs_client, tmp_path):
        """With > 100 failed charts and no expand flag, only the collapsed header is shown."""
        charts = [_make_failed_chart(f"chart-{i}") for i in range(101)]
        job = _create_job_with_result(_result_data(failed=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Failed Charts (101)" in page
        assert "chart-0" not in page

    def test_over_100_failed_charts_renders_full_table_with_expand(self, admin_jobs_client, tmp_path):
        """With > 100 failed charts and expand_all=True, the full table is rendered."""
        charts = [_make_failed_chart(f"chart-{i}") for i in range(101)]
        job = _create_job_with_result(_result_data(failed=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}/expand")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Failed Charts (101)" in page
        assert "chart-0" in page

    def test_no_failed_charts_section_absent(self, admin_jobs_client, tmp_path):
        """When there are no failed charts, the Failed Charts section is not rendered."""
        job = _create_job_with_result(_result_data(failed=[]), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Failed Charts" not in page


# ─────────────────────────────────────────────────────────────────────────────
# Skipped charts section
# ─────────────────────────────────────────────────────────────────────────────


class TestSkippedChartsSection:
    def test_small_list_renders_full_table(self, admin_jobs_client, tmp_path):
        """With <= 100 skipped charts, the full table is rendered."""
        charts = [_make_skipped_chart(f"chart-{i}") for i in range(4)]
        job = _create_job_with_result(_result_data(skipped=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Skipped Charts (4)" in page
        assert "chart-0" in page

    def test_exactly_100_skipped_charts_renders_full_table(self, admin_jobs_client, tmp_path):
        """Boundary: exactly 100 skipped charts renders the full table."""
        charts = [_make_skipped_chart(f"chart-{i}") for i in range(100)]
        job = _create_job_with_result(_result_data(skipped=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Skipped Charts (100)" in page
        assert "chart-0" in page

    def test_over_100_skipped_charts_collapses_without_expand(self, admin_jobs_client, tmp_path):
        """With > 100 skipped charts and no expand flag, only the collapsed header is shown."""
        charts = [_make_skipped_chart(f"chart-{i}") for i in range(101)]
        job = _create_job_with_result(_result_data(skipped=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Skipped Charts (101)" in page
        assert "chart-0" not in page

    def test_over_100_skipped_charts_renders_full_table_with_expand(self, admin_jobs_client, tmp_path):
        """With > 100 skipped charts and expand_all=True, the full table is rendered."""
        charts = [_make_skipped_chart(f"chart-{i}") for i in range(101)]
        job = _create_job_with_result(_result_data(skipped=charts), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}/expand")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Skipped Charts (101)" in page
        assert "chart-0" in page

    def test_no_skipped_charts_section_absent(self, admin_jobs_client, tmp_path):
        """When there are no skipped charts, the Skipped Charts section is not rendered."""
        job = _create_job_with_result(_result_data(skipped=[]), tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Skipped Charts" not in page


# ─────────────────────────────────────────────────────────────────────────────
# Mixed sections (regression: all three sections can coexist)
# ─────────────────────────────────────────────────────────────────────────────


class TestMixedChartSections:
    def test_all_three_sections_render_with_small_counts(self, admin_jobs_client, tmp_path):
        """All three sections render their full tables when each has <= 100 items."""
        result_data = _result_data(
            updated=[_make_chart("u-chart")],
            failed=[_make_failed_chart("f-chart")],
            skipped=[_make_skipped_chart("s-chart")],
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Updated Charts (1)" in page
        assert "Failed Charts (1)" in page
        assert "Skipped Charts (1)" in page
        assert "u-chart" in page
        assert "f-chart" in page
        assert "s-chart" in page

    def test_large_updated_collapses_while_small_failed_skipped_expand(self, admin_jobs_client, tmp_path):
        """Large updated_charts collapses while small failed/skipped still show full tables."""
        result_data = _result_data(
            updated=[_make_chart(f"u-{i}") for i in range(101)],
            failed=[_make_failed_chart("f-chart")],
            skipped=[_make_skipped_chart("s-chart")],
        )
        job = _create_job_with_result(result_data, tmp_path)

        response = admin_jobs_client.get(f"/admin/jobs/{_JOB_TYPE}/{job.id}")
        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        # Updated collapsed
        assert "Updated Charts (101)" in page
        assert "u-0" not in page
        # Failed and skipped still show full tables
        assert "f-chart" in page
        assert "s-chart" in page
