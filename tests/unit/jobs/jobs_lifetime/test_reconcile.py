"""Tests for ``jobs_lifetime.reconcile``."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from requests import HTTPError
from src.main_app.jobs.jobs_lifetime.reconcile import reconcile, setup_reconcile_schedule, sync_job

MODULE = "src.main_app.jobs.jobs_lifetime.reconcile"


def _patch_class(monkeypatch: pytest.MonkeyPatch, name: str) -> MagicMock:
    _mock_class = MagicMock()
    _mock_class.return_value = MagicMock()
    monkeypatch.setattr(f"{MODULE}.{name}", _mock_class)
    return _mock_class


@pytest.fixture
def mock_jobs_service_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = _patch_class(monkeypatch, "JobsService")
    _mock_class.return_value.FINAL_STATUSES = ("completed", "failed", "cancelled")
    _mock_class.return_value.list_active.return_value = []
    return _mock_class


@pytest.fixture
def mock_tf_service_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = _patch_class(monkeypatch, "ToolforgeJobsService")
    _mock_class.return_value.list_jobs.return_value = SimpleNamespace(jobs=[])
    return _mock_class


@pytest.fixture
def mock_backend_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    return _patch_class(monkeypatch, "ToolforgeBackend")


@pytest.fixture
def mock_sync_job(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(f"{MODULE}.sync_job", _mock)
    return _mock


@pytest.fixture
def mock_get_settings(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock(
        return_value=SimpleNamespace(
            jobs=SimpleNamespace(toolforge_job_image="img", toolforge_job_script="run.sh"),
        )
    )
    monkeypatch.setattr(f"{MODULE}.get_settings", _mock)
    return _mock


@pytest.fixture
def make_tf_job() -> Callable[..., SimpleNamespace]:
    def _factory(name: str, short: str = "succeeded") -> SimpleNamespace:
        return SimpleNamespace(name=name, status=SimpleNamespace(short=short))

    return _factory


class TestSyncJob:
    def test_failed_pod_marks_the_job_failed_with_its_messages(
        self,
        mock_jobs_service_class: MagicMock,
        mock_backend_class: MagicMock,
        make_job_record,
    ) -> None:
        job = make_job_record(status="running")
        mock_backend_class.return_value.status.return_value = {"short": "failed", "messages": ["oom", "killed"]}

        sync_job(job, mock_backend_class.return_value)

        mock_jobs_service_class.return_value.mark_failed.assert_called_once_with(job, "oom; killed")

    @pytest.mark.parametrize(("job_status", "completes"), [("pending", True), ("running", True), ("cancelled", False)])
    def test_succeeded_pod_only_completes_active_jobs(
        self,
        mock_jobs_service_class: MagicMock,
        mock_backend_class: MagicMock,
        make_job_record,
        job_status: str,
        completes: bool,
    ) -> None:
        job = make_job_record(status=job_status)
        mock_backend_class.return_value.status.return_value = {"short": "succeeded", "messages": []}

        sync_job(job, mock_backend_class.return_value)

        assert mock_jobs_service_class.return_value.mark_as_completed.called is completes

    def test_running_pod_promotes_a_pending_job(
        self,
        mock_jobs_service_class: MagicMock,
        mock_backend_class: MagicMock,
        make_job_record,
    ) -> None:
        job = make_job_record(status="pending")
        mock_backend_class.return_value.status.return_value = {"short": "running", "messages": []}

        sync_job(job, mock_backend_class.return_value)

        mock_jobs_service_class.return_value.update_job_status.assert_called_once_with(7, "running", job_type="demo")

    def test_running_pod_leaves_a_running_job_alone(
        self,
        mock_jobs_service_class: MagicMock,
        mock_backend_class: MagicMock,
        make_job_record,
    ) -> None:
        mock_backend_class.return_value.status.return_value = {"short": "running", "messages": []}

        sync_job(make_job_record(status="running"), mock_backend_class.return_value)

        mock_jobs_service_class.return_value.update_job_status.assert_not_called()

    def test_missing_pod_within_the_grace_period_is_left_alone(
        self,
        mock_jobs_service_class: MagicMock,
        mock_backend_class: MagicMock,
        make_job_record,
    ) -> None:
        job = make_job_record(created_at=datetime.now(UTC))
        mock_backend_class.return_value.status.return_value = None

        sync_job(job, mock_backend_class.return_value)

        mock_jobs_service_class.return_value.mark_failed.assert_not_called()

    @pytest.mark.parametrize("tzinfo", [UTC, None], ids=["aware", "naive-treated-as-utc"])
    def test_missing_pod_after_the_grace_period_is_failed(
        self,
        mock_jobs_service_class: MagicMock,
        mock_backend_class: MagicMock,
        make_job_record,
        tzinfo,
    ) -> None:
        created = datetime.now(UTC) - timedelta(minutes=10)
        job = make_job_record(created_at=created if tzinfo else created.replace(tzinfo=None))
        mock_backend_class.return_value.status.return_value = None

        sync_job(job, mock_backend_class.return_value)

        mock_jobs_service_class.return_value.mark_failed.assert_called_once_with(job, "job is missing in Toolforge")

    def test_creates_a_backend_when_none_is_given(
        self,
        mock_jobs_service_class: MagicMock,
        mock_backend_class: MagicMock,
        make_job_record,
    ) -> None:
        mock_backend_class.return_value.status.return_value = {"short": "running", "messages": []}

        sync_job(make_job_record(status="running"))

        mock_backend_class.assert_called_once_with()


class TestReconcile:
    def test_syncs_every_active_job_with_one_shared_backend(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        mock_backend_class: MagicMock,
        mock_sync_job: MagicMock,
        make_job_record,
    ) -> None:
        first, second = make_job_record(id=1), make_job_record(id=2)
        mock_jobs_service_class.return_value.list_active.return_value = [first, second]

        reconcile()

        mock_jobs_service_class.return_value.list_active.assert_called_once_with(backend="toolforge")
        mock_backend_class.assert_called_once_with(svc=mock_tf_service_class.return_value)
        backend = mock_backend_class.return_value
        assert [c.args for c in mock_sync_job.call_args_list] == [(first, backend), (second, backend)]

    def test_one_failing_sync_does_not_stop_the_others(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        mock_backend_class: MagicMock,
        mock_sync_job: MagicMock,
        make_job_record,
    ) -> None:
        mock_jobs_service_class.return_value.list_active.return_value = [make_job_record(id=1), make_job_record(id=2)]
        mock_sync_job.side_effect = [RuntimeError("api"), None]

        reconcile()

        assert mock_sync_job.call_count == 2

    def test_listing_failure_skips_the_cleanup(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        mock_backend_class: MagicMock,
    ) -> None:
        mock_tf_service_class.return_value.list_jobs.side_effect = RuntimeError("api down")

        reconcile()

        mock_tf_service_class.return_value.delete_job.assert_not_called()


class TestCleanup:
    @pytest.fixture(autouse=True)
    def _deps(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        mock_backend_class: MagicMock,
    ) -> None:
        """Every cleanup test needs the three class mocks."""

    def _run(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        tf_jobs: list,
        row,
    ) -> MagicMock:
        mock_tf_service_class.return_value.list_jobs.return_value = SimpleNamespace(jobs=tf_jobs)
        mock_jobs_service_class.return_value.get_by.return_value = row
        reconcile()
        return mock_tf_service_class.return_value

    def test_deletes_a_finished_pod_whose_row_is_final(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        make_tf_job,
        make_job_record,
    ) -> None:
        tf = self._run(
            mock_jobs_service_class,
            mock_tf_service_class,
            [make_tf_job("demo-7")],
            make_job_record(id=7, job_type="demo", status="completed"),
        )

        tf.delete_job.assert_called_once_with("demo-7")

    def test_never_deletes_a_pod_whose_name_does_not_round_trip(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        make_tf_job,
        make_job_record,
    ) -> None:
        tf = self._run(
            mock_jobs_service_class,
            mock_tf_service_class,
            [make_tf_job("someone-elses-7")],
            make_job_record(id=7, job_type="demo", status="completed"),
        )

        tf.delete_job.assert_not_called()

    @pytest.mark.parametrize("short", ["running", "pending"])
    def test_skips_pods_that_are_not_finished(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        make_tf_job,
        make_job_record,
        short: str,
    ) -> None:
        tf = self._run(
            mock_jobs_service_class,
            mock_tf_service_class,
            [make_tf_job("demo-7", short)],
            make_job_record(id=7, job_type="demo", status="completed"),
        )

        tf.delete_job.assert_not_called()

    def test_skips_pods_whose_row_is_still_active(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        make_tf_job,
        make_job_record,
    ) -> None:
        tf = self._run(
            mock_jobs_service_class,
            mock_tf_service_class,
            [make_tf_job("demo-7")],
            make_job_record(id=7, job_type="demo", status="running"),
        )

        tf.delete_job.assert_not_called()

    @pytest.mark.parametrize("name", ["reconcile-jobs", "nodash", ""])
    def test_skips_names_without_a_numeric_id(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        make_tf_job,
        name: str,
    ) -> None:
        tf = self._run(mock_jobs_service_class, mock_tf_service_class, [make_tf_job(name)], None)

        tf.delete_job.assert_not_called()
        mock_jobs_service_class.return_value.get_by.assert_not_called()

    def test_skips_pods_without_a_db_row(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        make_tf_job,
    ) -> None:
        tf = self._run(mock_jobs_service_class, mock_tf_service_class, [make_tf_job("demo-7")], None)

        tf.delete_job.assert_not_called()

    def test_delete_error_does_not_stop_the_cleanup(
        self,
        mock_jobs_service_class: MagicMock,
        mock_tf_service_class: MagicMock,
        make_tf_job,
        make_job_record,
    ) -> None:
        mock_tf_service_class.return_value.delete_job.side_effect = [HTTPError("500"), None]
        mock_jobs_service_class.return_value.get_by.side_effect = [
            make_job_record(id=1, job_type="demo", status="completed"),
            make_job_record(id=2, job_type="demo", status="completed"),
        ]
        mock_tf_service_class.return_value.list_jobs.return_value = SimpleNamespace(
            jobs=[make_tf_job("demo-1"), make_tf_job("demo-2")]
        )

        reconcile()

        assert mock_tf_service_class.return_value.delete_job.call_count == 2


class TestSetupReconcileSchedule:
    def test_creates_a_scheduled_job_running_reconcile(
        self,
        mock_tf_service_class: MagicMock,
        mock_get_settings: MagicMock,
    ) -> None:
        setup_reconcile_schedule()

        body = mock_tf_service_class.return_value.update_job.call_args.args[0]
        assert body["name"] == "reconcile-jobs"
        assert body["job_type"] == "scheduled"
        assert body["schedule"] == "*/5 * * * *"
        assert body["imagename"] == "img"
        assert body["cmd"] == "bash run.sh reconcile-jobs"
