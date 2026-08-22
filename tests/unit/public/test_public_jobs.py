"""Unit tests for src/main_app/public/public_jobs.py module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.main_app.database.exceptions import DuplicateRecordError
from src.main_app.database.models import JobRecord
from src.main_app.database.services import JobsService
from src.main_app.public.public_jobs import PublicJobsRoutes
from src.main_app.public.shared_jobs_routes import SharedJobRoutes

MOCK_URL = "/redirected"


@dataclass
class MockJobRoutesDeps:
    flash: MagicMock = field(default_factory=MagicMock)
    redirect: MagicMock = field(default_factory=MagicMock)
    url_for: MagicMock = field(default_factory=MagicMock)
    render_template: MagicMock = field(default_factory=MagicMock)
    get_current_user: MagicMock = field(default_factory=MagicMock)
    can_manage_job: MagicMock = field(default_factory=MagicMock)
    cancel_job_worker: MagicMock = field(default_factory=MagicMock)
    load_auth_payload: MagicMock = field(default_factory=MagicMock)
    start_job: MagicMock = field(default_factory=MagicMock)
    load_job_result: MagicMock = field(default_factory=MagicMock)
    get_job: MagicMock = field(default_factory=MagicMock)
    list_jobs: MagicMock = field(default_factory=MagicMock)
    delete_job_by_id_and_type: MagicMock = field(default_factory=MagicMock)
    delete_job: MagicMock = field(default_factory=MagicMock)
    get_all_settings_ready: MagicMock = field(default_factory=MagicMock)
    admin_load_user: MagicMock = field(default_factory=MagicMock)


@pytest.fixture
def mock_deps(
    monkeypatch: pytest.MonkeyPatch,
    mock_user: MagicMock,
    mock_job: MagicMock,
) -> MockJobRoutesDeps:
    deps = MockJobRoutesDeps()
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.flash", deps.flash)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.redirect", deps.redirect)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.url_for", deps.url_for)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.render_template", deps.render_template)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.get_current_user", deps.get_current_user)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.SharedJobRoutes.can_manage_job", deps.can_manage_job)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.cancel_job_worker", deps.cancel_job_worker)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.load_auth_payload", deps.load_auth_payload)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.start_job_form", deps.start_job)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.load_job_result", deps.load_job_result)

    deps.redirect.return_value = "redirected"
    deps.url_for.return_value = MOCK_URL
    deps.render_template.return_value = "rendered"
    deps.get_current_user.return_value = mock_user
    deps.can_manage_job.return_value = True
    deps.cancel_job_worker.return_value = False
    deps.load_auth_payload.return_value = {"token": "abc"}
    deps.start_job.return_value = 42

    return deps


@pytest.fixture
def mock_job() -> MagicMock:
    job = MagicMock()
    job.id = 1
    job.job_type = "test_job"
    job.username = "testuser"
    job.status = "running"
    job.result_file = None
    return job


@pytest.fixture
def mock_user() -> MagicMock:
    user = MagicMock()
    user.username = "testuser"
    user.is_active_admin = False
    return user


@pytest.fixture
def mock_admin() -> MagicMock:
    user = MagicMock()
    user.username = "admin"
    user.is_active_admin = True
    return user


@pytest.fixture
def mock_jobs_data() -> dict[str, MagicMock]:
    return {
        "test_job": MagicMock(
            job_type="test_job",
            job_list_template="test_list.html",
            job_details_template="test_detail.html",
            job_name="Test Job",
            start_confirm_message="Start?",
        ),
    }


@pytest.fixture
def mock_template_data() -> MagicMock:
    td = MagicMock()
    td.job_type = "test_job"
    td.job_list_template = "test_list.html"
    td.job_details_template = "test_detail.html"
    td.job_name = "Test Job"
    td.start_confirm_message = "Start?"
    td.load_settings = False
    td.form_class = None
    return td


@pytest.fixture
def mock_p_app(mock_jobs_data: dict[str, MagicMock], tmp_path: Any) -> Flask:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "test_list.html").write_text("list_{{ template_data.job_type }}_{{ template_data.job_name }}")

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
    return mock_p_app.test_client()


@pytest.fixture
def jobs_service() -> JobsService:
    return JobsService()


@pytest.fixture
def seeded_job(jobs_service: JobsService) -> JobRecord:
    return jobs_service.create_job("test_job", "testuser")


@pytest.fixture
def seeded_job_with_result(seeded_job: JobRecord, jobs_service: JobsService) -> JobRecord:
    return jobs_service.update_job_status(seeded_job.id, "completed", result_file="result.json", job_type="test_job")


# =========================================================================
# cancel_job_handler
# =========================================================================


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test."""
        self.service = SharedJobRoutes(bp_name="public_jobs")


class TestCancelJob(TestSetup):

    def test_not_logged_in(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.get_current_user.return_value = None
        result = self.service.cancel_job_handler(1, "test_job")
        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with("You must be logged in to cancel jobs.", "danger")

    def test_job_not_found(self, mock_deps: MockJobRoutesDeps) -> None:
        result = self.service.cancel_job_handler(999, "test_job")
        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with("Job not found.", "warning")

    def test_no_permission(self, mock_deps: MockJobRoutesDeps, seeded_job: JobRecord) -> None:
        mock_deps.can_manage_job.return_value = False
        result = self.service.cancel_job_handler(seeded_job.id, "test_job")
        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with("You don't have permission to cancel this job.", "danger")

    def test_cancel_successful(self, mock_deps: MockJobRoutesDeps, seeded_job: JobRecord) -> None:
        mock_deps.cancel_job_worker.return_value = True
        result = self.service.cancel_job_handler(seeded_job.id, "test_job")
        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with(f"Job {seeded_job.id} cancellation requested.", "success")

    def test_cancel_fails(self, mock_deps: MockJobRoutesDeps, seeded_job: JobRecord) -> None:
        result = self.service.cancel_job_handler(seeded_job.id, "test_job")
        assert result == "job_detail"
        mock_deps.flash.assert_called_once_with(f"Job {seeded_job.id} is not running or already cancelled.", "warning")


# =========================================================================
# delete_job_handler
# =========================================================================


class TestDeleteJob(TestSetup):
    def test_delete_successful(self, mock_deps: MockJobRoutesDeps, seeded_job: JobRecord) -> None:
        result = self.service.delete_job_handler(seeded_job.id, "test_job")
        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with(f"Job {seeded_job.id} deleted successfully.", "success")

    def test_cancel_then_delete(self, mock_deps: MockJobRoutesDeps, seeded_job: JobRecord) -> None:
        mock_deps.cancel_job_worker.return_value = True
        result = self.service.delete_job_handler(seeded_job.id, "test_job")
        assert result == "jobs_list"
        mock_deps.flash.assert_called_once_with(f"Job {seeded_job.id} deleted successfully.", "success")


# =========================================================================
# start_job_handler
# =========================================================================


class TestStartJob(TestSetup):
    def test_not_logged_in(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.get_current_user.return_value = None
        result = self.service.start_job_handler("test_job", {})
        assert result is None
        mock_deps.flash.assert_called_once_with("You must be logged in to start this job.", "danger")

    def test_auth_payload_failure(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.load_auth_payload.side_effect = RuntimeError("OAuth error")
        result = self.service.start_job_handler("test_job", {})
        assert result is None
        mock_deps.flash.assert_called_once_with("Failed to load auth payload. Please try again.", "danger")

    def test_duplicate_job_error(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.start_job.side_effect = DuplicateRecordError()
        result = self.service.start_job_handler("test_job", {})
        assert result is None
        mock_deps.flash.assert_called_once_with(
            "A job of this type is already running. Please wait for it to complete.", "warning"
        )

    def test_generic_exception(self, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.start_job.side_effect = ValueError("unexpected")
        result = self.service.start_job_handler("test_job", {})
        assert result is None
        mock_deps.flash.assert_called_once_with("Failed to start job. Please try again.", "danger")

    def test_successful_start(self, mock_deps: MockJobRoutesDeps) -> None:
        result = self.service.start_job_handler("test_job", {})
        assert result == 42
        mock_deps.flash.assert_called_once_with("Job 42 started to test_job.", "success")


# =========================================================================
# jobs_list_handler
# =========================================================================


class TestJobsList(TestSetup):
    def test_normal_listing(
        self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock, seeded_job: JobRecord
    ) -> None:
        result = self.service.jobs_list_handler(mock_template_data)

        assert result == "rendered"
        mock_deps.flash.assert_not_called()
        mock_deps.render_template.assert_called_once_with(
            "test_list.html",
            jobs=[seeded_job],
            template_data=mock_template_data,
            form=None,
            bp_name="public_jobs",
        )

    def test_listing_with_0_jobs(self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock) -> None:

        result = self.service.jobs_list_handler(mock_template_data)
        assert result == "rendered"
        mock_deps.render_template.assert_called_once()
        _args, kwargs = mock_deps.render_template.call_args
        assert kwargs["jobs"] == []

    def test_exception_falls_back_to_empty(self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock) -> None:

        result = self.service.jobs_list_handler(mock_template_data)
        assert result == "rendered"
        mock_deps.flash.assert_not_called()
        mock_deps.render_template.assert_called_once()
        _args, kwargs = mock_deps.render_template.call_args
        assert kwargs["jobs"] == []


# =========================================================================
# job_detail_handler
# =========================================================================


class TestJobDetail(TestSetup):
    def test_job_found_without_result(
        self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock, seeded_job: JobRecord
    ) -> None:
        mock_deps.load_job_result.return_value = None

        result = self.service.job_detail_handler(seeded_job.id, mock_template_data)

        assert result == "rendered"
        mock_deps.render_template.assert_called_once_with(
            "test_detail.html",
            job=seeded_job,
            result_data=None,
            template_data=mock_template_data,
            bp_name="public_jobs",
        )

    def test_job_found_with_result(
        self,
        mock_deps: MockJobRoutesDeps,
        mock_template_data: MagicMock,
        seeded_job_with_result: JobRecord,
    ) -> None:
        mock_deps.load_job_result.return_value = {"key": "value"}

        result = self.service.job_detail_handler(seeded_job_with_result.id, mock_template_data)

        assert result == "rendered"
        mock_deps.render_template.assert_called_once_with(
            "test_detail.html",
            job=seeded_job_with_result,
            result_data={"key": "value"},
            template_data=mock_template_data,
            bp_name="public_jobs",
        )

    def test_job_not_found(self, mock_deps: MockJobRoutesDeps, mock_template_data: MagicMock) -> None:
        result = self.service.job_detail_handler(999, mock_template_data)
        assert result == "redirected"
        mock_deps.flash.assert_called_once_with("Job id 999 was not found", "warning")
        mock_deps.redirect.assert_called_once()


# =========================================================================
# Route integration tests
# =========================================================================


class TestJobsPublicRoutesRoutes(TestSetup):
    """Integration tests for routes registered by PublicJobsRoutes.

    These tests use a standalone Flask app (mock_p_app) with custom templates
    but rely on mocked DB services because the standalone app does not have
    SQLAlchemy initialized.  The handler-level tests above already verify
    real DB behavior.
    """

    @pytest.fixture(autouse=True)
    def _common_mocks(self, monkeypatch: pytest.MonkeyPatch, mock_deps: MockJobRoutesDeps, mock_job: MagicMock) -> None:
        """Set up mocks so routes can execute without a real database."""
        from flask import redirect as _real_redirect
        from flask import render_template as _real_render_template
        from flask import url_for as _real_url_for

        monkeypatch.setattr("src.main_app.public.shared_jobs_routes.render_template", _real_render_template)
        monkeypatch.setattr("src.main_app.public.shared_jobs_routes.redirect", _real_redirect)
        monkeypatch.setattr("src.main_app.public.shared_jobs_routes.url_for", _real_url_for)

        monkeypatch.setattr("src.main_app.public.shared_jobs_routes.JobsService.get_job", mock_deps.get_job)
        monkeypatch.setattr("src.main_app.public.shared_jobs_routes.JobsService.list_jobs", mock_deps.list_jobs)
        monkeypatch.setattr(
            "src.main_app.public.shared_jobs_routes.JobsService.delete_job_by_id_and_type",
            mock_deps.delete_job_by_id_and_type,
        )
        monkeypatch.setattr("src.main_app.public.shared_jobs_routes.JobsService.delete", mock_deps.delete_job)
        monkeypatch.setattr(
            "src.main_app.public.shared_jobs_routes.SettingsService.get_all_settings_ready",
            mock_deps.get_all_settings_ready,
        )

        mock_deps.get_job.return_value = mock_job
        mock_deps.list_jobs.return_value = [mock_job]
        mock_deps.delete_job_by_id_and_type.return_value = True
        mock_deps.delete_job.return_value = True

        mock_deps.cancel_job_worker.return_value = True
        mock_deps.load_job_result.return_value = {"result": "ok"}

        monkeypatch.setattr("src.main_app.public.auth.decorators.get_current_user", mock_deps.get_current_user)

        mock_deps.admin_load_user = MagicMock(return_value=MagicMock(username="admin", is_active_admin=True))
        monkeypatch.setattr("src.main_app.admin.decorators.get_current_user", mock_deps.admin_load_user)

    def test_jobs_list_200(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/test_job")
        assert resp.status_code == 200
        assert b"test_job" in resp.data

    def test_jobs_list_unknown_job_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/nonexistent_type")
        assert resp.status_code == 404

    def test_job_detail_200(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/test_job/1")
        assert resp.status_code == 200
        assert b"detail" in resp.data

    def test_job_detail_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/nonexistent_type/1")
        assert resp.status_code == 404

    def test_job_detail_expand_200(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/test_job/1/expand")
        assert resp.status_code == 200
        assert b"True" in resp.data

    def test_job_detail_expand_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.get("/jobs/nonexistent_type/1/expand")
        assert resp.status_code == 404

    def test_cancel_job_302(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/test_job/1/cancel")
        assert resp.status_code == 302

    def test_cancel_job_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/nonexistent_type/1/cancel")
        assert resp.status_code == 404

    def test_cancel_job_not_logged_in(self, mock_p_client: Flask.test_client, mock_deps: MockJobRoutesDeps) -> None:
        mock_deps.get_current_user.return_value = None
        resp = mock_p_client.post("/jobs/test_job/1/cancel")
        assert resp.status_code == 500

    def test_start_job_302(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/test_job/start", data={"key": "value"})
        assert resp.status_code == 302

    def test_start_job_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/nonexistent_type/start", data={"key": "value"})
        assert resp.status_code == 404

    def test_start_job_failure_redirects_to_list(
        self, mock_p_client: Flask.test_client, mock_deps: MockJobRoutesDeps
    ) -> None:
        mock_deps.start_job.side_effect = DuplicateRecordError()
        resp = mock_p_client.post("/jobs/test_job/start", data={"key": "value"})
        assert resp.status_code == 302

    def test_delete_job_302(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/test_job/1/delete")
        assert resp.status_code == 302

    def test_delete_job_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/nonexistent_type/1/delete")
        assert resp.status_code == 404

    def test_delete_job_not_admin_403(self, mock_p_client: Flask.test_client, mock_deps: MockJobRoutesDeps) -> None:
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
