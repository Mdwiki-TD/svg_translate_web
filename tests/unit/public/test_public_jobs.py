"""Unit tests for src/main_app/public/public_jobs.py module.

Tests cover direct calls to module-level functions (cancel_job_handler, delete_job_handler,
start_job_handler, jobs_list_handler, job_detail_handler) and route integration via test client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.main_app.db.exceptions import DuplicateJobError
from src.main_app.public.jobs_routes_utils import (
    cancel_job_handler,
    delete_job_handler,
    job_detail_handler,
    jobs_list_handler,
    start_job_handler,
)
from src.main_app.public.public_jobs import PublicJobsRoutes

# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture(autouse=True)
def setup_db():
    """Override conftest's autouse setup_db — no database needed for these unit tests."""


@pytest.fixture
def mock_job() -> MagicMock:
    """Return a generic running job owned by testuser."""
    job = MagicMock()
    job.id = 1
    job.job_type = "test_job"
    job.username = "testuser"
    job.status = "running"
    job.result_file = None
    return job


@pytest.fixture
def mock_job_with_result() -> MagicMock:
    """Return a completed job that has a result_file."""
    job = MagicMock()
    job.id = 2
    job.job_type = "test_job"
    job.username = "testuser"
    job.status = "completed"
    job.result_file = "result_2.json"
    return job


@pytest.fixture
def mock_user() -> MagicMock:
    """Return a non-admin authenticated user."""
    user = MagicMock()
    user.username = "testuser"
    user.is_active_admin = False
    return user


@pytest.fixture
def mock_admin() -> MagicMock:
    """Return an admin (coordinator) user."""
    user = MagicMock()
    user.username = "admin"
    user.is_active_admin = True
    return user


@pytest.fixture
def mock_jobs_data() -> dict[str, MagicMock]:
    """Return a mock jobs_data_infos dictionary with one job type."""
    return {
        "test_job": MagicMock(
            job_list_template="test_list.html",
            job_details_template="test_detail.html",
            job_name="Test Job",
            start_confirm_message="Start?",
        ),
    }


@pytest.fixture
def mock_template_data() -> MagicMock:
    """Return a single JobData-like object for direct function calls."""
    td = MagicMock()
    td.job_list_template = "test_list.html"
    td.job_details_template = "test_detail.html"
    td.job_name = "Test Job"
    td.start_confirm_message = "Start?"
    return td


@pytest.fixture
def mock_p_app(mock_jobs_data: dict[str, MagicMock], tmp_path: Any) -> Flask:
    """Create a minimal Flask app with the PublicJobsRoutes blueprint registered."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "test_list.html").write_text("list_{{ job_type }}_{{ list_title }}")
    (templates_dir / "test_detail.html").write_text("detail_{{ job_id }}_{{ job_type }}_{{ expand_all }}")

    app = Flask(__name__, template_folder=str(templates_dir))
    app.secret_key = "test"

    module = PublicJobsRoutes(
        bp=Blueprint("public_jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=mock_jobs_data,
        bp_name="public_jobs",
    )
    app.register_blueprint(module.bp)
    return app


@pytest.fixture
def mock_p_client(mock_p_app: Flask):
    """Return a test client for the minimal Flask app."""
    return mock_p_app.test_client()


@dataclass
class MockJobRoutesDeps:
    """Typed bundle of all mocked jobs_routes_utils dependencies."""

    flash: MagicMock = field(default_factory=MagicMock)
    redirect: MagicMock = field(default_factory=MagicMock)
    url_for: MagicMock = field(default_factory=MagicMock)
    render_template: MagicMock = field(default_factory=MagicMock)
    load_user: MagicMock = field(default_factory=MagicMock)
    get_job: MagicMock = field(default_factory=MagicMock)
    list_jobs: MagicMock = field(default_factory=MagicMock)
    can_manage_job: MagicMock = field(default_factory=MagicMock)
    cancel_job_worker: MagicMock = field(default_factory=MagicMock)
    load_auth_payload: MagicMock = field(default_factory=MagicMock)
    start_job: MagicMock = field(default_factory=MagicMock)
    delete_job_by_id_and_type: MagicMock = field(default_factory=MagicMock)
    delete_job: MagicMock = field(default_factory=MagicMock)
    load_job_result: MagicMock = field(default_factory=MagicMock)
    admin_load_user: MagicMock = field(default_factory=MagicMock)


@pytest.fixture
def mock_deps(
    monkeypatch: pytest.MonkeyPatch,
    mock_user: MagicMock,
    mock_job: MagicMock,
) -> MockJobRoutesDeps:
    """Patch all jobs_routes_utils dependencies and return a typed bundle."""
    _m = "src.main_app.public.jobs_routes_utils"

    deps = MockJobRoutesDeps()
    monkeypatch.setattr(f"{_m}.flash", deps.flash)
    monkeypatch.setattr(f"{_m}.redirect", deps.redirect)
    monkeypatch.setattr(f"{_m}.url_for", deps.url_for)
    monkeypatch.setattr(f"{_m}.render_template", deps.render_template)
    monkeypatch.setattr(f"{_m}.load_user", deps.load_user)
    monkeypatch.setattr(f"{_m}.can_manage_job", deps.can_manage_job)
    monkeypatch.setattr(f"{_m}.cancel_job_worker", deps.cancel_job_worker)
    monkeypatch.setattr(f"{_m}.load_auth_payload", deps.load_auth_payload)
    monkeypatch.setattr(f"{_m}.start_job", deps.start_job)
    monkeypatch.setattr(f"{_m}.JobsService.get_job", deps.get_job)
    monkeypatch.setattr(f"{_m}.JobsService.list_jobs", deps.list_jobs)
    monkeypatch.setattr(f"{_m}.JobsService.delete_job_by_id_and_type", deps.delete_job_by_id_and_type)
    monkeypatch.setattr(f"{_m}.JobsService.delete", deps.delete_job)
    monkeypatch.setattr(f"{_m}.load_job_result", deps.load_job_result)

    deps.redirect.return_value = "redirected"
    deps.url_for.return_value = MOCK_URL
    deps.render_template.return_value = "rendered"
    deps.load_user.return_value = mock_user
    deps.get_job.return_value = mock_job
    deps.list_jobs.return_value = [mock_job]
    deps.can_manage_job.return_value = True
    deps.cancel_job_worker.return_value = False
    deps.load_auth_payload.return_value = {"token": "abc"}
    deps.start_job.return_value = 42
    deps.delete_job_by_id_and_type.return_value = True
    deps.delete_job.return_value = True

    return deps


# =========================================================================
# cancel_job_handler
# =========================================================================


MOCK_URL = "/redirected"


class TestCancelJob:
    """Direct tests for cancel_job_handler()."""

    def test_not_logged_in(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.load_user.return_value = None

        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with("You must be logged in to cancel jobs.", "danger")

    def test_job_not_found(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.get_job.side_effect = LookupError("not found")

        result = cancel_job_handler(1, "test_job")

        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with("Job not found.", "warning")

    def test_no_permission(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.can_manage_job.return_value = False

        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with("You don't have permission to cancel this job.", "danger")

    def test_cancel_successful(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.cancel_job_worker.return_value = True

        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with("Job 1 cancellation requested.", "success")

    def test_cancel_fails(self, mock_deps: MockJobRoutesDeps) -> None:
        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with("Job 1 is not running or already cancelled.", "warning")


# =========================================================================
# delete_job_handler
# =========================================================================


class TestDeleteJob:
    """Direct tests for delete_job_handler()."""

    def test_delete_successful(self, mock_deps: MockJobRoutesDeps) -> None:
        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with("Job 1 deleted successfully.", "success")

    def test_cancel_then_delete(self, mock_deps: MockJobRoutesDeps) -> None:
        """When cancel_job_worker returns True, the job is still deleted."""
        mock_deps.cancel_job_worker.return_value = True

        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with("Job 1 deleted successfully.", "success")

    def test_delete_failure(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.delete_job_by_id_and_type.return_value = False

        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with("Failed to delete job 1", "danger")

    def test_exception_during_delete(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.delete_job_by_id_and_type.side_effect = RuntimeError("DB error")

        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with("Failed to delete job 1", "danger")


# =========================================================================
# start_job_handler
# =========================================================================


class TestStartJob:
    """Direct tests for start_job_handler()."""

    def test_not_logged_in(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.load_user.return_value = None

        result = start_job_handler("test_job", {})

        assert result is None
        mock_deps.flash.assert_called_once_with("You must be logged in to start this job.", "danger")

    def test_auth_payload_failure(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.load_auth_payload.side_effect = RuntimeError("OAuth error")

        result = start_job_handler("test_job", {})

        assert result is None
        mock_deps.flash.assert_called_once_with("Failed to load auth payload. Please try again.", "danger")

    def test_duplicate_job_error(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.start_job.side_effect = DuplicateJobError()

        result = start_job_handler("test_job", {})

        assert result is None
        mock_deps.flash.assert_called_once_with(
            "A job of this type is already running. Please wait for it to complete.", "warning"
        )

    def test_generic_exception(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.start_job.side_effect = ValueError("unexpected")

        result = start_job_handler("test_job", {})

        assert result is None
        mock_deps.flash.assert_called_once_with("Failed to start job. Please try again.", "danger")

    def test_successful_start(self, mock_deps: MockJobRoutesDeps) -> None:
        result = start_job_handler("test_job", {})

        assert result == 42
        mock_deps.flash.assert_called_once_with("Job 42 started to test_job.", "success")


# =========================================================================
# jobs_list_handler
# =========================================================================


class TestJobsList:
    """Direct tests for jobs_list_handler()."""

    def test_normal_listing(self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock) -> None:
        mock_jobs = [MagicMock(id=1), MagicMock(id=2)]
        mock_deps.list_jobs.return_value = mock_jobs

        result = jobs_list_handler("test_job", mock_template_data)

        assert result == "rendered"
        mock_deps.flash.assert_not_called()
        mock_deps.render_template.assert_called_once_with(
            "test_list.html",
            jobs=mock_jobs,
            job_type="test_job",
            list_title="Test Job",
            list_headline="Test Job",
            start_confirm_message="Start?",
        )

    def test_listing_with_0_jobs(self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock) -> None:
        mock_deps.list_jobs.return_value = []

        result = jobs_list_handler("test_job", mock_template_data)

        assert result == "rendered"
        mock_deps.render_template.assert_called_once()
        _args, kwargs = mock_deps.render_template.call_args
        assert kwargs["jobs"] == []

    def test_exception_falls_back_to_empty(
        self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock
    ) -> None:
        mock_deps.list_jobs.side_effect = RuntimeError("DB error")

        result = jobs_list_handler("test_job", mock_template_data)

        assert result == "rendered"
        mock_deps.flash.assert_called_once_with("Unable to load jobs list.", "danger")
        _args, kwargs = mock_deps.render_template.call_args
        assert kwargs["jobs"] == []


# =========================================================================
# job_detail_handler
# =========================================================================


class TestJobDetail:
    """Direct tests for job_detail_handler()."""

    def test_job_found_without_result(
        self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock
    ) -> None:
        mock_deps.load_job_result.return_value = None

        result = job_detail_handler(1, "test_job", mock_template_data, "public_jobs")

        assert result == "rendered"
        mock_deps.render_template.assert_called_once_with(
            "test_detail.html",
            job=mock_deps.get_job.return_value,
            job_type="test_job",
            result_data=None,
            detail_title="Test Job",
            detail_headline="Test Job",
            expand_all=False,
        )

    def test_job_found_with_result(
        self,
        mock_deps: MockJobRoutesDeps,
        mock_job_with_result: MagicMock,
        mock_template_data: MagicMock,
    ) -> None:
        mock_deps.get_job.return_value = mock_job_with_result
        mock_deps.load_job_result.return_value = {"key": "value"}

        result = job_detail_handler(2, "test_job", mock_template_data, "public_jobs")

        assert result == "rendered"
        mock_deps.render_template.assert_called_once_with(
            "test_detail.html",
            job=mock_job_with_result,
            job_type="test_job",
            result_data={"key": "value"},
            detail_title="Test Job",
            detail_headline="Test Job",
            expand_all=False,
        )

    def test_job_found_with_expand_all(
        self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock
    ) -> None:
        mock_deps.load_job_result.return_value = None

        result = job_detail_handler(1, "test_job", mock_template_data, "public_jobs", expand_all=True)

        assert result == "rendered"
        mock_deps.render_template.assert_called_once_with(
            "test_detail.html",
            job=mock_deps.get_job.return_value,
            job_type="test_job",
            result_data=None,
            detail_title="Test Job",
            detail_headline="Test Job",
            expand_all=True,
        )

    def test_job_not_found(self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock) -> None:
        mock_deps.get_job.side_effect = LookupError("Job id 99 was not found")

        result = job_detail_handler(99, "test_job", mock_template_data, "public_jobs")

        assert result == "redirected"
        mock_deps.flash.assert_called_once_with("Job id 99 was not found", "warning")
        mock_deps.redirect.assert_called_once()


# =========================================================================
# Route integration tests
# =========================================================================


class TestJobsPublicRoutesRoutes:
    """Integration tests for routes registered by PublicJobsRoutes."""

    @pytest.fixture(autouse=True)
    def _common_mocks(self, monkeypatch: pytest.MonkeyPatch, mock_deps: MockJobRoutesDeps) -> None:
        """Set up common mocks so routes can execute without a real database.

        Individual tests can override specific mocks for their scenario.
        jobs_routes_utils.* is already patched by the mock_deps fixture.
        """
        # Re-patch Flask functions with real implementations — integration tests need them
        from flask import redirect as _real_redirect
        from flask import render_template as _real_render_template
        from flask import url_for as _real_url_for

        _m = "src.main_app.public.jobs_routes_utils"
        monkeypatch.setattr(f"{_m}.render_template", _real_render_template)
        monkeypatch.setattr(f"{_m}.redirect", _real_redirect)
        monkeypatch.setattr(f"{_m}.url_for", _real_url_for)

        mock_deps.cancel_job_worker.return_value = True
        mock_deps.load_job_result.return_value = {"result": "ok"}

        monkeypatch.setattr("src.main_app.public.auth.utils.load_user", mock_deps.load_user)

        # Allow delete route's @admin_required decorator to pass by default
        mock_deps.admin_load_user = MagicMock(
            return_value=MagicMock(username="admin", is_active_admin=True)
        )
        monkeypatch.setattr("src.main_app.admin.decorators.load_user", mock_deps.admin_load_user)

    # ── jobs_list ──────────────────────────────────────────────────────

    def test_jobs_list_200(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/test_job")
        assert resp.status_code == 200
        assert b"test_job" in resp.data

    def test_jobs_list_unknown_job_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/nonexistent_type")
        assert resp.status_code == 404

    # ── job_detail ─────────────────────────────────────────────────────

    def test_job_detail_200(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/test_job/1")
        assert resp.status_code == 200
        assert b"detail" in resp.data

    def test_job_detail_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/nonexistent_type/1")
        assert resp.status_code == 404

    # ── job_detail_expand ──────────────────────────────────────────────

    def test_job_detail_expand_200(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/test_job/1/expand")
        assert resp.status_code == 200
        assert b"True" in resp.data

    def test_job_detail_expand_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/nonexistent_type/1/expand")
        assert resp.status_code == 404

    # ── cancel_job ─────────────────────────────────────────────────────

    def test_cancel_job_302(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/test_job/1/cancel")
        assert resp.status_code == 302

    def test_cancel_job_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/nonexistent_type/1/cancel")
        assert resp.status_code == 404

    def test_cancel_job_not_logged_in(
        self, mock_p_client: Flask.test_client, mock_deps: MockJobRoutesDeps
    ) -> None:
        mock_deps.load_user.return_value = None
        resp = mock_p_client.post("/jobs/test_job/1/cancel")
        assert resp.status_code == 302

    # ── start_job ──────────────────────────────────────────────────────

    def test_start_job_302(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/test_job/start", data={"key": "value"})
        assert resp.status_code == 302

    def test_start_job_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/nonexistent_type/start", data={"key": "value"})
        assert resp.status_code == 404

    def test_start_job_failure_redirects_to_list(
        self, mock_p_client: Flask.test_client, mock_deps: MockJobRoutesDeps
    ) -> None:
        mock_deps.start_job.side_effect = DuplicateJobError()
        resp = mock_p_client.post("/jobs/test_job/start", data={"key": "value"})
        assert resp.status_code == 302

    # ── delete_job ─────────────────────────────────────────────────────

    def test_delete_job_302(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/test_job/1/delete")
        assert resp.status_code == 302

    def test_delete_job_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/nonexistent_type/1/delete")
        assert resp.status_code == 404

    def test_delete_job_not_admin_403(
        self, mock_p_client: Flask.test_client, mock_deps: MockJobRoutesDeps
    ) -> None:
        mock_deps.admin_load_user.return_value = MagicMock(username="regular", is_active_admin=False)
        resp = mock_p_client.post("/jobs/test_job/1/delete")
        assert resp.status_code == 403

    def test_delete_job_not_logged_in_302(
        self, mock_p_client: Flask.test_client, mock_deps: MockJobRoutesDeps, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_deps.admin_load_user.return_value = None
        monkeypatch.setattr(
            "src.main_app.admin.decorators.url_for",
            lambda endpoint, **values: f"/{endpoint}",
        )
        resp = mock_p_client.post("/jobs/test_job/1/delete")
        assert resp.status_code == 302
