"""Unit tests for src/main_app/public/public_jobs.py module.

Tests cover direct calls to module-level functions (cancel_job_handler, delete_job_handler,
start_job_handler, jobs_list_handler, job_detail_handler) and route integration via test client.
"""

from __future__ import annotations

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


# =========================================================================
# cancel_job_handler
# =========================================================================


MOCK_URL = "/redirected"


class TestCancelJob:
    """Direct tests for cancel_job_handler()."""

    def _setup_mocks(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
        flash = MagicMock()
        redirect = MagicMock(return_value="redirected")
        url_for = MagicMock(return_value=MOCK_URL)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", flash)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.redirect", redirect)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.url_for", url_for)
        return {"flash": flash, "redirect": redirect, "url_for": url_for}

    def test_not_logged_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: None)

        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mocks["flash"].assert_called_once_with("You must be logged in to cancel jobs.", "danger")

    def test_job_not_found(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.get_job",
            MagicMock(side_effect=LookupError("not found")),
        )

        result = cancel_job_handler(1, "test_job")

        assert result == "jobs_list"
        mocks["flash"].assert_called_once_with("Job not found.", "warning")

    def test_no_permission(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda j, u: False)

        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mocks["flash"].assert_called_once_with("You don't have permission to cancel this job.", "danger")

    def test_cancel_successful(
        self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock
    ) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda j, u: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.cancel_job_worker", lambda jid, jt, j: True)

        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mocks["flash"].assert_called_once_with("Job 1 cancellation requested.", "success")

    def test_cancel_fails(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda j, u: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.cancel_job_worker", lambda jid, jt, j: False)

        result = cancel_job_handler(1, "test_job")

        assert result == "job_detail"
        mocks["flash"].assert_called_once_with("Job 1 is not running or already cancelled.", "warning")


# =========================================================================
# delete_job_handler
# =========================================================================


class TestDeleteJob:
    """Direct tests for delete_job_handler()."""

    def _setup_mocks(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
        flash = MagicMock()
        redirect = MagicMock(return_value="redirected")
        url_for = MagicMock(return_value=MOCK_URL)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", flash)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.redirect", redirect)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.url_for", url_for)
        return {"flash": flash, "redirect": redirect, "url_for": url_for}

    def test_delete_successful(
        self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock
    ) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda j, u: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.cancel_job_worker", lambda jid, jt, j: False)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.JobsService.delete_job", lambda self, jid, jt: True)

        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mocks["flash"].assert_called_once_with("Job 1 deleted successfully.", "success")

    def test_cancel_then_delete(
        self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock
    ) -> None:
        """When cancel_job_worker returns True, the job is still deleted."""
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda j, u: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.cancel_job_worker", lambda jid, jt, j: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.JobsService.delete_job", lambda self, jid, jt: True)

        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mocks["flash"].assert_called_once_with("Job 1 deleted successfully.", "success")

    def test_delete_failure(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda j, u: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.cancel_job_worker", lambda jid, jt, j: False)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.JobsService.delete_job", lambda self, jid, jt: False)

        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mocks["flash"].assert_called_once_with("Failed to delete job 1", "danger")

    def test_exception_during_delete(
        self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock
    ) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda j, u: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.cancel_job_worker", lambda jid, jt, j: False)
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.JobsService.delete_job",
            MagicMock(side_effect=RuntimeError("DB error")),
        )

        result = delete_job_handler(1, "test_job")

        assert result == "jobs_list"
        mocks["flash"].assert_called_once_with("Failed to delete job 1", "danger")


# =========================================================================
# start_job_handler
# =========================================================================


class TestStartJob:
    """Direct tests for start_job_handler()."""

    def _setup_mocks(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
        flash = MagicMock()
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", flash)
        return {"flash": flash}

    def test_not_logged_in(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: None)

        result = start_job_handler("test_job", {})

        assert result is None
        mocks["flash"].assert_called_once_with("You must be logged in to start this job.", "danger")

    def test_auth_payload_failure(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.load_auth_payload",
            MagicMock(side_effect=RuntimeError("OAuth error")),
        )

        result = start_job_handler("test_job", {})

        assert result is None
        mocks["flash"].assert_called_once_with("Failed to load auth payload. Please try again.", "danger")

    def test_duplicate_job_error(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_auth_payload", lambda u: {"token": "abc"})
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.start_job",
            MagicMock(side_effect=DuplicateJobError()),
        )

        result = start_job_handler("test_job", {})

        assert result is None
        mocks["flash"].assert_called_once_with(
            "A job of this type is already running. Please wait for it to complete.", "warning"
        )

    def test_generic_exception(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_auth_payload", lambda u: {"token": "abc"})
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.start_job",
            MagicMock(side_effect=ValueError("unexpected")),
        )

        result = start_job_handler("test_job", {})

        assert result is None
        mocks["flash"].assert_called_once_with("Failed to start job. Please try again.", "danger")

    def test_successful_start(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_auth_payload", lambda u: {"token": "abc"})
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.start_job", lambda au, jt, args: 42)

        result = start_job_handler("test_job", {})

        assert result == 42
        mocks["flash"].assert_called_once_with("Job 42 started to test_job.", "success")


# =========================================================================
# jobs_list_handler
# =========================================================================


class TestJobsList:
    """Direct tests for jobs_list_handler()."""

    def _setup_mocks(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
        flash = MagicMock()
        render_template = MagicMock(return_value="rendered")
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", flash)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.render_template", render_template)
        return {"flash": flash, "render_template": render_template}

    def test_normal_listing(self, monkeypatch: pytest.MonkeyPatch, mock_template_data: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        mock_jobs = [MagicMock(id=1), MagicMock(id=2)]
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.list_jobs", lambda limit, job_type: mock_jobs)

        result = jobs_list_handler("test_job", mock_template_data)

        assert result == "rendered"
        mocks["flash"].assert_not_called()
        mocks["render_template"].assert_called_once_with(
            "test_list.html",
            jobs=mock_jobs,
            job_type="test_job",
            list_title="Test Job",
            list_headline="Test Job",
            start_confirm_message="Start?",
        )

    def test_listing_with_0_jobs(self, monkeypatch: pytest.MonkeyPatch, mock_template_data: MagicMock) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.list_jobs", lambda limit, job_type: [])

        result = jobs_list_handler("test_job", mock_template_data)

        assert result == "rendered"
        mocks["render_template"].assert_called_once()
        _args, kwargs = mocks["render_template"].call_args
        assert kwargs["jobs"] == []

    def test_exception_falls_back_to_empty(
        self, monkeypatch: pytest.MonkeyPatch, mock_template_data: MagicMock
    ) -> None:
        mocks = self._setup_mocks(monkeypatch)
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.list_jobs",
            MagicMock(side_effect=RuntimeError("DB error")),
        )

        result = jobs_list_handler("test_job", mock_template_data)

        assert result == "rendered"
        mocks["flash"].assert_called_once_with("Unable to load jobs list.", "danger")
        _args, kwargs = mocks["render_template"].call_args
        assert kwargs["jobs"] == []


# =========================================================================
# job_detail_handler
# =========================================================================


class TestJobDetail:
    """Direct tests for job_detail_handler()."""

    def _setup_mocks(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
        self._flash = MagicMock()
        self._redirect = MagicMock(return_value="redirected")
        self._url_for = MagicMock(return_value=MOCK_URL)
        self._render_template = MagicMock(return_value="rendered")
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.flash", self._flash)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.redirect", self._redirect)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.url_for", self._url_for)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.render_template", self._render_template)

    def test_job_found_without_result(
        self, monkeypatch: pytest.MonkeyPatch, mock_job: MagicMock, mock_template_data: MagicMock
    ) -> None:
        self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_job_result", lambda rf: None)

        result = job_detail_handler(1, "test_job", mock_template_data, "public_jobs")

        assert result == "rendered"
        self._render_template.assert_called_once_with(
            "test_detail.html",
            job=mock_job,
            job_type="test_job",
            result_data=None,
            detail_title="Test Job",
            detail_headline="Test Job",
            expand_all=False,
        )

    def test_job_found_with_result(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_job_with_result: MagicMock,
        mock_template_data: MagicMock,
    ) -> None:
        self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job_with_result)
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.load_job_result",
            lambda rf: {"key": "value"},
        )

        result = job_detail_handler(2, "test_job", mock_template_data, "public_jobs")

        assert result == "rendered"
        self._render_template.assert_called_once_with(
            "test_detail.html",
            job=mock_job_with_result,
            job_type="test_job",
            result_data={"key": "value"},
            detail_title="Test Job",
            detail_headline="Test Job",
            expand_all=False,
        )

    def test_job_found_with_expand_all(
        self, monkeypatch: pytest.MonkeyPatch, mock_job: MagicMock, mock_template_data: MagicMock
    ) -> None:
        self._setup_mocks(monkeypatch)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_job_result", lambda rf: None)

        result = job_detail_handler(1, "test_job", mock_template_data, "public_jobs", expand_all=True)

        assert result == "rendered"
        self._render_template.assert_called_once_with(
            "test_detail.html",
            job=mock_job,
            job_type="test_job",
            result_data=None,
            detail_title="Test Job",
            detail_headline="Test Job",
            expand_all=True,
        )

    def test_job_not_found(self, monkeypatch: pytest.MonkeyPatch, mock_template_data: MagicMock) -> None:
        self._setup_mocks(monkeypatch)
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.get_job",
            MagicMock(side_effect=LookupError("Job id 99 was not found")),
        )

        result = job_detail_handler(99, "test_job", mock_template_data, "public_jobs")

        assert result == "redirected"
        self._flash.assert_called_once_with("Job id 99 was not found", "warning")
        self._redirect.assert_called_once()


# =========================================================================
# Route integration tests
# =========================================================================


class TestJobsPublicRoutesRoutes:
    """Integration tests for routes registered by PublicJobsRoutes."""

    @pytest.fixture(autouse=True)
    def _common_mocks(self, monkeypatch: pytest.MonkeyPatch, mock_user: MagicMock, mock_job: MagicMock) -> None:
        """Set up common mocks so routes can execute without a real database.

        Individual tests can override specific mocks for their scenario.
        """
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: mock_user)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.get_job", lambda jid, jt: mock_job)
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.list_jobs",
            lambda limit, job_type: [mock_job],
        )
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.can_manage_job", lambda job, user: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_auth_payload", lambda u: {"token": "abc"})
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.cancel_job_worker", lambda *a: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.start_job", lambda au, jt, args: 42)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.JobsService.delete", lambda jid, jt: True)
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_job_result", lambda rf: {"result": "ok"})

        monkeypatch.setattr("src.main_app.public.auth.utils.load_user", lambda: mock_user)

        # Allow delete route's @admin_required decorator to pass by default
        _admin_user = MagicMock(username="admin", is_active_admin=True)
        monkeypatch.setattr("src.main_app.admin.decorators.load_user", lambda: _admin_user)
        self._mock_user = mock_user

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

    def test_cancel_job_not_logged_in(self, mock_p_client: Flask.test_client, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", lambda: None)
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
        self, mock_p_client: Flask.test_client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "src.main_app.public.jobs_routes_utils.start_job",
            MagicMock(side_effect=DuplicateJobError()),
        )
        resp = mock_p_client.post("/jobs/test_job/start", data={"key": "value"})
        assert resp.status_code == 302

    # ── delete_job ─────────────────────────────────────────────────────

    def test_delete_job_302(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/test_job/1/delete")
        assert resp.status_code == 302

    def test_delete_job_unknown_type_404(self, mock_p_client: Flask.test_client) -> None:
        resp = mock_p_client.post("/jobs/nonexistent_type/1/delete")
        assert resp.status_code == 404

    def test_delete_job_not_admin_403(self, mock_p_client: Flask.test_client, monkeypatch: pytest.MonkeyPatch) -> None:
        non_admin = MagicMock(username="regular", is_active_admin=False)
        monkeypatch.setattr("src.main_app.admin.decorators.load_user", lambda: non_admin)
        resp = mock_p_client.post("/jobs/test_job/1/delete")
        assert resp.status_code == 403

    def test_delete_job_not_logged_in_302(
        self, mock_p_client: Flask.test_client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("src.main_app.admin.decorators.load_user", lambda: None)
        monkeypatch.setattr(
            "src.main_app.admin.decorators.url_for",
            lambda endpoint, **values: f"/{endpoint}",
        )
        resp = mock_p_client.post("/jobs/test_job/1/delete")
        assert resp.status_code == 302
