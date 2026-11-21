"""Integration tests for queue state in the admin jobs UI."""

from __future__ import annotations

from html import unescape
from unittest.mock import Mock

import pytest
from src.main_app.database.services import JobsService
from src.main_app.jobs_workers.jobs_lifetime.jobs_queue import EnqueueResult

pytestmark = [pytest.mark.integration]

JOB_TYPE = "collect_templates_data"


@pytest.fixture
def mock_flash(monkeypatch: pytest.MonkeyPatch) -> Mock:
    _mock = Mock()
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.flash", _mock)
    return _mock


@pytest.fixture
def mock_submit_job(monkeypatch: pytest.MonkeyPatch) -> Mock:
    _mock = Mock()
    _mock.submit_form = Mock(return_value=EnqueueResult(job_id=1, queued=False))
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.JobStarter", Mock(return_value=_mock))
    return _mock.submit_form


@pytest.fixture
def mock_load_auth_payload(monkeypatch: pytest.MonkeyPatch) -> Mock:
    _mock = Mock()
    _mock.return_value = {"username": "admin_user"}
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.RequestContextHelper.load_auth_payload", _mock)
    return _mock


@pytest.fixture
def mock_cancel_event(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Keep cancellation away from the thread registry (no job runs here)."""
    _mock = Mock(return_value=None)
    monkeypatch.setattr("src.main_app.jobs_workers.jobs_lifetime.jobs_canceller.get_cancel_event", _mock)
    return _mock


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = JobsService()


class TestQueueUi(TestSetup):
    def test_list_shows_running_and_queued_positions(self, admin_jobs_client) -> None:
        running = self.service.enqueue_job(JOB_TYPE, "admin_user")
        self.service.claim_pending_job(running.id)
        second = self.service.enqueue_job(JOB_TYPE, "admin_user")
        third = self.service.enqueue_job(JOB_TYPE, "admin_user")

        response = admin_jobs_client.get(f"/admin_panel/jobs/{JOB_TYPE}")

        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Running" in page
        assert "Queued · #1" in page
        assert "Queued · #2" in page
        assert str(second.id) in page
        assert str(third.id) in page

    def test_list_without_pending_jobs_shows_no_queue_labels(self, admin_jobs_client) -> None:
        job = self.service.enqueue_job(JOB_TYPE, "admin_user")
        self.service.claim_pending_job(job.id)
        self.service.update_job_status(job.id, "completed", job_type=JOB_TYPE)

        response = admin_jobs_client.get(f"/admin_panel/jobs/{JOB_TYPE}")

        page = unescape(response.get_data(as_text=True))
        assert "Queued ·" not in page
        assert "Completed" in page

    def test_detail_page_shows_queue_position(self, admin_jobs_client) -> None:
        running = self.service.enqueue_job(JOB_TYPE, "admin_user")
        self.service.claim_pending_job(running.id)
        queued = self.service.enqueue_job(JOB_TYPE, "admin_user")

        response = admin_jobs_client.get(f"/admin_panel/jobs/{JOB_TYPE}/{queued.id}")

        assert response.status_code == 200
        page = unescape(response.get_data(as_text=True))
        assert "Queued · #1" in page

    def test_queued_job_can_be_cancelled(self, admin_jobs_client, mock_flash, mock_cancel_event) -> None:
        running = self.service.enqueue_job(JOB_TYPE, "admin_user")
        self.service.claim_pending_job(running.id)
        queued = self.service.enqueue_job(JOB_TYPE, "admin_user")

        response = admin_jobs_client.post(f"/admin_panel/jobs/{JOB_TYPE}/{queued.id}/cancel")

        assert response.status_code == 302
        mock_flash.assert_any_call(f"Job {queued.id} cancellation requested.", "success")

        cancelled = self.service.get_job(queued.id, JOB_TYPE)
        assert cancelled.status == "cancelled"
        # The running job keeps executing and keeps the active slot
        assert self.service.get_job(running.id, JOB_TYPE).status == "running"

    def test_cancel_pending_job_moves_queue_positions(self, admin_jobs_client, mock_flash, mock_cancel_event) -> None:
        running = self.service.enqueue_job(JOB_TYPE, "admin_user")
        self.service.claim_pending_job(running.id)
        second = self.service.enqueue_job(JOB_TYPE, "admin_user")
        third = self.service.enqueue_job(JOB_TYPE, "admin_user")

        admin_jobs_client.post(f"/admin_panel/jobs/{JOB_TYPE}/{second.id}/cancel")

        assert self.service.get_queue_position(second.id) == 0
        assert self.service.get_queue_position(third.id) == 1


class TestSubmissionFeedback(TestSetup):
    def test_started_job_flash_message(
        self, admin_jobs_client, mock_flash, mock_submit_job, mock_load_auth_payload
    ) -> None:
        mock_submit_job.return_value = EnqueueResult(job_id=7, queued=False)

        response = admin_jobs_client.post(f"/admin_panel/jobs/{JOB_TYPE}/start")

        assert response.status_code == 302
        mock_flash.assert_any_call(f"Job 7 started to {JOB_TYPE}.", "success")

    def test_queued_job_flash_message_shows_position(
        self, admin_jobs_client, mock_flash, mock_submit_job, mock_load_auth_payload
    ) -> None:
        mock_submit_job.return_value = EnqueueResult(job_id=8, queued=True, position=3)

        response = admin_jobs_client.post(f"/admin_panel/jobs/{JOB_TYPE}/start")

        assert response.status_code == 302
        mock_flash.assert_any_call("Your job has been added to the queue. Its current position is 3.", "info")

    def test_queued_job_redirects_to_detail(self, admin_jobs_client, mock_submit_job, mock_load_auth_payload) -> None:
        mock_submit_job.return_value = EnqueueResult(job_id=9, queued=True, position=1)

        response = admin_jobs_client.post(f"/admin_panel/jobs/{JOB_TYPE}/start")

        assert response.status_code == 302
        assert response.headers["Location"].endswith(f"/admin_panel/jobs/{JOB_TYPE}/9")
