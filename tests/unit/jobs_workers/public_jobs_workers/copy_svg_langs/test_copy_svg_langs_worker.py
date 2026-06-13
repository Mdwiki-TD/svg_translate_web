"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
    copy_svg_langs_worker_entry,
)
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import (
    CopySvgLangsWorkerObject,
    FilesProcessedItem,
)

@pytest.fixture
def mock_worker_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker",
        _mock_class,
    )
    return _mock_class


class TestCopySvgLangsWorker:
    def test_get_job_type(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
        )
        assert worker.get_job_type() == "copy_svg_langs"

    def test_initial_result_structure(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
        )
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.title is None
        assert result.stages.text.status == "Pending"
        assert result.stages.titles.status == "Pending"
        assert result.stages.translations.status == "Pending"
        assert result.stages.download.status == "Pending"
        assert result.stages.nested.status == "Pending"
        assert result.stages.inject.status == "Pending"
        assert result.stages.upload.status == "Pending"

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = CopySvgLangsWorker(
            job_id=1,
            args={"title": "Test.svg"},
            user=user,
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
            cancel_event=cancel_event,
        )
        assert worker.cancel_event is cancel_event

    def test_worker_reads_upload_limit_from_args(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg", "upload_limit": 5},
        )
        assert worker.upload_limit == 5

    def test_worker_defaults_upload_limit_when_args_none(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args=None,
        )
        assert worker.upload_limit == 0

    def test_worker_upload_limit_none_when_key_missing(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
        )
        assert worker.upload_limit == 0


class TestCopySvgLangsWorkerEntry:
    def test_worker_entry_missing_title(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            args={"title": ""},
            user=None,
        )

    def test_worker_entry_missing_args(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            args={"title": "Test.svg"},
            user=None,
        )

    def test_worker_entry_creates_worker(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=123,
            args={"title": "Test.svg"},
            user={"id": 1},
        )

        mock_worker_class.assert_called_once_with(
            job_id=123,
            args={"title": "Test.svg"},
            user={"id": 1},
            cancel_event=None,
        )
        mock_worker_class.return_value.run.assert_called_once()

    def test_worker_entry_with_cancel_event(self, mock_worker_class) -> None:
        cancel_event = threading.Event()

        copy_svg_langs_worker_entry(
            job_id=456,
            args={"title": "Another.svg"},
            user=None,
            cancel_event=cancel_event,
        )

        _, kwargs = mock_worker_class.call_args
        assert kwargs["cancel_event"] is cancel_event

    def test_worker_entry_args_is_keyword_only(self, mock_worker_class) -> None:
        with pytest.raises(TypeError):
            copy_svg_langs_worker_entry(1, None, {"title": "Test.svg"})  # type: ignore

        copy_svg_langs_worker_entry(job_id=1, user=None, args={"title": "Test.svg"})

        mock_worker_class.assert_called_once_with(
            job_id=1,
            args={"title": "Test.svg"},
            user=None,
            cancel_event=None,
        )
        mock_worker_class.return_value.run.assert_called_once()

    def test_worker_entry_args_defaults_to_none(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(job_id=99, user={"username": "tester"})

        mock_worker_class.assert_called_once_with(
            job_id=99,
            args=None,
            user={"username": "tester"},
            cancel_event=None,
        )

    def test_worker_entry_user_is_second_positional(self, mock_worker_class) -> None:
        user = {"username": "testuser"}

        copy_svg_langs_worker_entry(job_id=123, user=user)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["user"] is user

    def test_worker_entry_maps_copy_svg_langs_upload_limit(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            user=None,
            args={"upload_limit": 5},
        )

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"]["upload_limit"] == 5

    def test_worker_entry_does_not_map_when_key_absent(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            user=None,
            args={"other_key": "value"},
        )

        call_kwargs = mock_worker_class.call_args.kwargs
        assert "upload_limit" not in call_kwargs["args"]

    def test_worker_entry_does_not_modify_args_when_none(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(job_id=1, user=None, args=None)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"] is None


@pytest.fixture
def mock_steps():
    with (
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step") as m_text,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step") as m_titles,
        patch(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step"
        ) as m_trans,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step") as m_down,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step") as m_nested,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step") as m_inject,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_step") as m_upload,
    ):
        yield {
            "text": m_text,
            "titles": m_titles,
            "translations": m_trans,
            "download": m_down,
            "nested": m_nested,
            "inject": m_inject,
            "upload": m_upload,
        }


@pytest.fixture
def mock_clients():
    with (
        patch(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.create_commons_session"
        ) as m_session,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.get_user_site") as m_site,
    ):
        m_session.return_value = MagicMock()
        m_site.return_value = MagicMock()
        yield {"session": m_session, "site": m_site}


@pytest.fixture
def worker():
    user = {"username": "testuser", "id": 123}
    args = {"title": "File:Test.svg", "upload": True}
    _worker = CopySvgLangsWorker(job_id=1, user=user, args=args)
    _worker._save_progress = MagicMock()
    return _worker


class TestCopySvgLangsWorkerProcess:
    def test_process_no_title(self, worker: CopySvgLangsWorker, mock_clients):
        worker.title = None
        result: CopySvgLangsWorkerObject = worker.process()
        assert result.status == "failed"

    def test_process_success(self, worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]}
        mock_steps["translations"].return_value = {"success": True, "translations": {"new": {"en": "Text"}}}
        mock_steps["download"].return_value = {"success": True, "files_dict": {"File1.svg": "path/1"}}
        mock_steps["nested"].return_value = {"success": True, "data": {}, "results": {}}
        mock_steps["inject"].return_value = {
            "success": True,
            "results": {"File1.svg": {"result": True}},
            "data": {"files": {"File1.svg": {"file_path": "path/1/injected"}}},
        }
        mock_steps["upload"].return_value = {
            "success": True,
            "summary": {"uploaded": 1, "failed": 0, "no_changes": 0},
            "errors": [],
            "results": {"File1.svg": {"result": True}},
        }

        result: CopySvgLangsWorkerObject = worker.process()

        # BaseObjectsJobWorker.run sets it to completed, but process() returns current state
        assert result.status == "pending"
        assert worker.result.stages.upload.status == "Completed"
        assert "upload_result" in result.results_summary

    def test_process_stage_fails(self, worker: CopySvgLangsWorker, mock_steps, mock_clients):
        mock_steps["text"].return_value = {"success": False, "error": "Extraction failed"}

        result: CopySvgLangsWorkerObject = worker.process()

        assert result.status == "failed"
        assert result.stages.text.status == "Failed"
        assert result.stages.text.message == "Extraction failed"

    def test_process_upload_disabled(self, worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path):
        worker.output_dir = tmp_path
        worker.args["upload"] = False

        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": []}
        mock_steps["translations"].return_value = {"success": True, "translations": {}}
        mock_steps["download"].return_value = {"success": True, "files_dict": {}}
        mock_steps["nested"].return_value = {"success": True, "data": {}, "results": {}}
        mock_steps["inject"].return_value = {"success": True, "results": {}, "data": {"files": {}}}

        result: CopySvgLangsWorkerObject = worker.process()

        assert result.stages.upload.status == "Skipped"
        assert result.stages.upload.message == "Upload disabled"

    def test_process_auth_failed(self, worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path):
        worker.output_dir = tmp_path
        mock_clients["site"].return_value = None

        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": []}
        mock_steps["translations"].return_value = {"success": True, "translations": {}}
        mock_steps["download"].return_value = {"success": True, "files_dict": {}}
        mock_steps["nested"].return_value = {"success": True, "data": {}, "results": {}}
        mock_steps["inject"].return_value = {"success": True, "results": {}, "data": {"files": {}}}

        result: CopySvgLangsWorkerObject = worker.process()

        assert result.stages.upload.status == "Failed"
        assert result.stages.upload.message == "Authentication failed"

    def test_process_cancelled(self, worker: CopySvgLangsWorker, mock_clients):
        with patch.object(CopySvgLangsWorker, "is_cancelled", return_value=True):
            result: CopySvgLangsWorkerObject = worker.process()
            assert result.stages.text.status == "Cancelled"

    def test_run_stage_exception(self, worker: CopySvgLangsWorker):
        def failing_step():
            raise ValueError("Boom")

        success = worker._run_stage(worker.result.stages.text, failing_step)
        assert success is False
        assert worker.result.stages.text.status == "Failed"
        assert "Boom" in worker.result.stages.text.message

    def test_compute_output_dir_none(self, worker: CopySvgLangsWorker):
        assert worker._compute_output_dir(None) is None

    def test_log_upload_error(self, worker: CopySvgLangsWorker):
        worker.result.files_processed = {
            "File1.svg": FilesProcessedItem(
                title="title",
                status="pending",
            )
        }
        # worker.result.files_processed["File1.svg"].steps.upload = StepResult(result=None, msg="")
        worker.log_upload_error("Some error", False, "Failed")

        assert worker.result.stages.upload.status == "Failed"
        assert worker.result.files_processed["File1.svg"].status == "Failed"
        assert worker.result.files_processed["File1.svg"].steps.upload.msg == "Some error"

    def test_save_files_stats_error(self, worker: CopySvgLangsWorker, tmp_path):
        worker.output_dir = tmp_path
        bad_path = tmp_path / "files_stats.json"
        bad_path.mkdir()

        # Should not raise exception
        worker._save_files_stats({"data": "test"})

    def test_save_files_stats_unexpected_exception(self, worker: CopySvgLangsWorker, tmp_path):
        worker.output_dir = tmp_path

        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.json.dump",
            side_effect=RuntimeError("unexpected"),
        ):
            worker._save_files_stats({"key": "value"})
