"""Tests for the Flask CLI commands in ``jobs.cli_jobs``."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from flask import Flask
from src.main_app.database.exceptions import DuplicateRecordError
from src.main_app.jobs.cli_jobs import EXIT_DUPLICATE_JOB, register_cli_jobs

MODULE = "src.main_app.jobs.cli_jobs"


@pytest.fixture
def cli_runner(flask_app: Flask) -> CliRunner:
    register_cli_jobs(flask_app)
    return flask_app.test_cli_runner()


@pytest.fixture
def mock_job_starter_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_instance.run_now.return_value = 0
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(f"{MODULE}.JobStarter", _mock_class)
    return _mock_class


@pytest.fixture
def mock_job_executor_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_instance.run.return_value = 0
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(f"{MODULE}.JobExecutor", _mock_class)
    return _mock_class


@pytest.fixture
def mock_reconcile(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr("src.main_app.jobs.jobs_lifetime.reconcile.reconcile", _mock)
    return _mock


class TestRunJob:
    def test_runs_the_job_inline_with_update_all_false_by_default(
        self,
        cli_runner: CliRunner,
        mock_job_starter_class: MagicMock,
    ) -> None:
        result = cli_runner.invoke(args=["run-job", "demo"])

        assert result.exit_code == 0
        mock_job_starter_class.return_value.run_now.assert_called_once_with("demo", args={"update_all": "false"})

    def test_update_all_flag(self, cli_runner: CliRunner, mock_job_starter_class: MagicMock) -> None:
        cli_runner.invoke(args=["run-job", "demo", "--update-all"])

        mock_job_starter_class.return_value.run_now.assert_called_once_with("demo", args={"update_all": "true"})

    @pytest.mark.parametrize("exit_code", [1, 2, 3])
    def test_exits_with_the_executor_exit_code(
        self,
        cli_runner: CliRunner,
        mock_job_starter_class: MagicMock,
        exit_code: int,
    ) -> None:
        mock_job_starter_class.return_value.run_now.return_value = exit_code

        assert cli_runner.invoke(args=["run-job", "demo"]).exit_code == exit_code

    def test_duplicate_active_job_exits_with_the_dedicated_code(
        self,
        cli_runner: CliRunner,
        mock_job_starter_class: MagicMock,
    ) -> None:
        mock_job_starter_class.return_value.run_now.side_effect = DuplicateRecordError()

        result = cli_runner.invoke(args=["run-job", "demo"])

        assert result.exit_code == EXIT_DUPLICATE_JOB == 4
        assert "already active" in result.output

    def test_unknown_job_type_exits_2_with_the_message(
        self,
        cli_runner: CliRunner,
        mock_job_starter_class: MagicMock,
    ) -> None:
        mock_job_starter_class.return_value.run_now.side_effect = ValueError("Unknown job type: x")

        result = cli_runner.invoke(args=["run-job", "x"])

        assert result.exit_code == 2
        assert "Unknown job type: x" in result.output


class TestRunJobId:
    def test_runs_the_job_with_signal_handlers_enabled(
        self,
        cli_runner: CliRunner,
        mock_job_executor_class: MagicMock,
    ) -> None:
        result = cli_runner.invoke(args=["run-job-id", "12"])

        assert result.exit_code == 0
        mock_job_executor_class.return_value.run.assert_called_once_with(12, install_signal_handlers=True)

    def test_exits_with_the_executor_exit_code(
        self,
        cli_runner: CliRunner,
        mock_job_executor_class: MagicMock,
    ) -> None:
        mock_job_executor_class.return_value.run.return_value = 3

        assert cli_runner.invoke(args=["run-job-id", "12"]).exit_code == 3

    def test_job_id_must_be_an_integer(self, cli_runner: CliRunner, mock_job_executor_class: MagicMock) -> None:
        assert cli_runner.invoke(args=["run-job-id", "abc"]).exit_code != 0
        mock_job_executor_class.return_value.run.assert_not_called()


class TestReconcileJobs:
    def test_calls_reconcile(self, cli_runner: CliRunner, mock_reconcile: MagicMock) -> None:
        result = cli_runner.invoke(args=["reconcile-jobs"])

        assert result.exit_code == 0
        mock_reconcile.assert_called_once_with()
