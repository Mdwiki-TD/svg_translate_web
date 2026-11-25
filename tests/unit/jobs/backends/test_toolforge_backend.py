"""Tests for ``backends.toolforge_backend``."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from requests import HTTPError
from src.main_app.jobs.backends.toolforge_backend import ToolforgeBackend, tf_job_name

MODULE = "src.main_app.jobs.backends.toolforge_backend"


@pytest.fixture
def app_settings() -> SimpleNamespace:
    return SimpleNamespace(
        jobs=SimpleNamespace(
            toolforge_job_image="default-image",
            toolforge_job_default_memory="1Gi",
            toolforge_job_default_cpu="0.5",
            toolforge_job_script="run.sh",
        )
    )


@pytest.fixture
def mock_tf_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def backend(mock_tf_service: MagicMock, app_settings: SimpleNamespace) -> ToolforgeBackend:
    return ToolforgeBackend(svc=mock_tf_service, app_settings=app_settings)


@pytest.fixture
def mock_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(f"{MODULE}.Path.home", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def make_http_error() -> Callable[[int | None], HTTPError]:
    def _factory(status_code: int | None) -> HTTPError:
        response = None if status_code is None else SimpleNamespace(status_code=status_code)
        return HTTPError("http error", response=response)

    return _factory


class TestTfJobName:
    @pytest.mark.parametrize(
        ("job_type", "job_id", "expected"),
        [
            ("demo", 7, "demo-7"),
            ("collect_templates_data", 5, "collect-templates-data-5"),
            ("My Job!", 5, "my-job-5"),
            ("..x..", 1, "x-1"),
            ("a" * 60, 9, f"{'a' * 40}-9"),
        ],
    )
    def test_builds_a_toolforge_compatible_name(self, job_type: str, job_id: int, expected: str) -> None:
        assert tf_job_name(job_type, job_id) == expected


class TestStart:
    def test_creates_a_one_off_job_that_runs_run_job_id(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        mock_home: Path,
        job_record,
        job_data,
    ) -> None:
        name = backend.start(job_record, job_data)

        assert name == "demo-7"
        body = mock_tf_service.create_job.call_args.args[0]
        assert body["name"] == "demo-7"
        assert body["cmd"] == "bash run.sh run-job-id 7"
        assert body["job_type"] == "one-off"
        assert body["retry"] == 0
        assert body["filelog_stdout"] == f"{mock_home}/data/logs/tfj_jobs/demo-7.out"
        assert body["filelog_stderr"] == f"{mock_home}/data/logs/tfj_jobs/demo-7.err"

    def test_uses_global_defaults_when_the_job_has_no_overrides(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        mock_home: Path,
        job_record,
        job_data,
    ) -> None:
        backend.start(job_record, job_data)

        body = mock_tf_service.create_job.call_args.args[0]
        assert (body["imagename"], body["memory"], body["cpu"]) == ("default-image", "1Gi", "0.5")

    def test_job_overrides_win_over_the_defaults(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        mock_home: Path,
        job_record,
        job_data,
    ) -> None:
        job_data.image, job_data.memory, job_data.cpu = "big-image", "4Gi", "2"

        backend.start(job_record, job_data)

        body = mock_tf_service.create_job.call_args.args[0]
        assert (body["imagename"], body["memory"], body["cpu"]) == ("big-image", "4Gi", "2")

    def test_ignores_the_user_because_the_pod_rebuilds_it(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        mock_home: Path,
        job_record,
        job_data,
    ) -> None:
        backend.start(job_record, job_data, user={"username": "alice", "access_token": "secret"})

        assert "secret" not in str(mock_tf_service.create_job.call_args)


class TestCancel:
    def test_deletes_the_toolforge_job(self, backend: ToolforgeBackend, mock_tf_service: MagicMock, job_record) -> None:
        assert backend.cancel(job_record) is True
        mock_tf_service.delete_job.assert_called_once_with("demo-7")

    def test_already_gone_counts_as_cancelled(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        make_http_error,
        job_record,
    ) -> None:
        mock_tf_service.delete_job.side_effect = make_http_error(404)

        assert backend.cancel(job_record) is True

    @pytest.mark.parametrize("status_code", [500, None])
    def test_other_http_errors_are_a_failure(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        make_http_error,
        job_record,
        status_code: int | None,
    ) -> None:
        mock_tf_service.delete_job.side_effect = make_http_error(status_code)

        assert backend.cancel(job_record) is False


class TestStatus:
    def test_returns_the_live_status_of_the_job(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        job_record,
    ) -> None:
        live = {"short": "running", "messages": []}
        mock_tf_service.show_job.return_value = SimpleNamespace(job=MagicMock(live_status=MagicMock(return_value=live)))

        assert backend.status(job_record) == live
        mock_tf_service.show_job.assert_called_once_with("demo-7")

    def test_404_means_the_job_is_not_in_toolforge(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        make_http_error,
        job_record,
    ) -> None:
        mock_tf_service.show_job.side_effect = make_http_error(404)

        assert backend.status(job_record) is None

    def test_other_http_errors_propagate(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        make_http_error,
        job_record,
    ) -> None:
        mock_tf_service.show_job.side_effect = make_http_error(500)

        with pytest.raises(HTTPError):
            backend.status(job_record)

    def test_empty_response_raises(self, backend: ToolforgeBackend, mock_tf_service: MagicMock, job_record) -> None:
        mock_tf_service.show_job.return_value = SimpleNamespace(job=None)

        with pytest.raises(RuntimeError, match="demo-7"):
            backend.status(job_record)


class TestLogs:
    def test_returns_only_the_last_lines(
        self, backend: ToolforgeBackend, mock_tf_service: MagicMock, job_record
    ) -> None:
        mock_tf_service.get_logs.return_value = "\n".join(f"line {i}" for i in range(10))

        assert backend.logs(job_record, tail=3) == "line 7\nline 8\nline 9"
        mock_tf_service.get_logs.assert_called_once_with("demo-7")

    def test_http_error_gives_empty_logs(
        self,
        backend: ToolforgeBackend,
        mock_tf_service: MagicMock,
        make_http_error,
        job_record,
    ) -> None:
        mock_tf_service.get_logs.side_effect = make_http_error(500)

        assert backend.logs(job_record) == ""
