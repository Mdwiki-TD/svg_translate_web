"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
)


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


class TestRunStageDetails:
    @pytest.fixture
    def worker(self):
        user = {"username": "testuser", "id": 123}
        args = {"title": "File:Test.svg", "upload": True}
        _worker = CopySvgLangsWorker(job_id=1, user=user, args=args)
        _worker._save_progress = MagicMock()
        return _worker

    def test_run_stage_sets_message_from_step_result(self, worker: CopySvgLangsWorker):
        def step():
            return {"success": True, "message": "Custom message"}

        success = worker._run_stage(worker.result.stages.text, step)

        assert success is True
        assert worker.result.stages.text.message == "Custom message"
        assert worker.result.stages.text.status == "Completed"

    def test_run_stage_summary_formatting(self, worker: CopySvgLangsWorker):
        from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import StageDetail

        stage = StageDetail(name="test", status="Pending", message="")

        def step():
            return {"success": True, "summary": {"total": 5, "fixed": 3}}

        success = worker._run_stage(stage, step)

        assert success is True
        assert "total: 5" in stage.message
        assert "fixed: 3" in stage.message

    def test_run_stage_summary_not_dict(self, worker: CopySvgLangsWorker):
        from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import StageDetail

        stage = StageDetail(name="test", status="Pending", message="")

        def step():
            return {"success": True, "summary": "not a dict"}

        success = worker._run_stage(stage, step)

        assert success is True
        assert stage.message == ""

    def test_run_stage_run_after_called(self, worker: CopySvgLangsWorker):
        after_called = []

        def step():
            return {"success": True}

        def after():
            after_called.append(True)

        worker._run_stage(worker.result.stages.text, step, run_after_func=after)

        assert after_called == [True]


class TestProcessStageFailures:
    @pytest.fixture
    def worker(self):
        user = {"username": "testuser", "id": 123}
        args = {"title": "File:Test.svg", "upload": True}
        _worker = CopySvgLangsWorker(job_id=1, user=user, args=args)
        _worker._save_progress = MagicMock()
        return _worker

    @pytest.fixture
    def mock_clients(self):
        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.create_commons_session"
            ) as m_session,
            patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.get_user_site") as m_site,
        ):
            m_session.return_value = MagicMock()
            m_site.return_value = MagicMock()
            yield {"session": m_session, "site": m_site}

    def test_process_titles_stage_fails(self, worker, mock_clients):
        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": False, "error": "No titles found"},
            ),
        ):
            result = worker.process()

        assert result.status == "failed"
        assert result.stages.titles.message == "No titles found"
        assert result.stages.titles.status == "Failed"

    def test_process_translations_stage_fails(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": False, "error": "No translations"},
            ),
        ):
            result = worker.process()

        assert result.status == "failed"
        assert result.stages.translations.status == "Failed"

    def test_process_download_stage_fails(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": False, "files_dict": {}, "files": [], "failed_titles": ["File1.svg"]},
            ),
        ):
            result = worker.process()

        assert result.status == "failed"
        assert result.stages.download.status == "Failed"

    def test_process_nested_stage_fails(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "path/1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": False, "data": {}, "results": {}},
            ),
        ):
            result = worker.process()

        assert result.status == "failed"
        assert result.stages.nested.status == "Failed"

    def test_process_inject_stage_fails(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "path/1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={"success": False, "results": {}, "data": {}},
            ),
        ):
            result = worker.process()

        assert result.status == "failed"
        assert result.stages.inject.status == "Failed"

    def test_process_upload_stage_fails(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "path/1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={
                    "success": True,
                    "results": {"File1.svg": {"result": True}},
                    "data": {"files": {"File1.svg": {"file_path": "path/1/injected"}}},
                },
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_step",
                return_value={
                    "success": False,
                    "summary": {"uploaded": 0, "failed": 1, "no_changes": 0},
                    "errors": ["error"],
                    "results": {"File1.svg": {"result": False, "msg": "Upload failed"}},
                },
            ),
        ):
            result = worker.process()

        assert result.status == "failed"
        assert result.stages.upload.status == "Failed"


class TestProcessProgressCallbacks:
    @pytest.fixture
    def worker(self):
        user = {"username": "testuser", "id": 123}
        args = {"title": "File:Test.svg", "upload": True}
        _worker = CopySvgLangsWorker(job_id=1, user=user, args=args)
        _worker._save_progress = MagicMock()
        return _worker

    @pytest.fixture
    def mock_clients(self):
        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.create_commons_session"
            ) as m_session,
            patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.get_user_site") as m_site,
        ):
            m_session.return_value = MagicMock()
            m_site.return_value = MagicMock()
            yield {"session": m_session, "site": m_site}

    def _make_download_side_effect(self):
        def side_effect(*args, **kwargs):
            cb = kwargs.get("progress_callback")
            if cb:
                cb(1, 1, "test msg", {"File1.svg": {"result": False, "msg": "Download failed"}})
            return {"success": True, "files_dict": {"File1.svg": "path/1"}, "files": ["path/1"]}

        return side_effect

    def test_download_progress_callback(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                side_effect=self._make_download_side_effect(),
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={"success": True, "results": {}, "data": {"files": {}}},
            ),
        ):
            worker.args["upload"] = False
            result = worker.process()

        assert "Downloading" in result.stages.download.message
        assert result.files_processed["File1.svg"].steps.download.msg == "Download failed"
        assert result.files_processed["File1.svg"].status == "failed"

    def _make_fix_nested_side_effect(self):
        def side_effect(*args, **kwargs):
            cb = kwargs.get("progress_callback")
            if cb:
                cb(10, 10, "nested msg", {"File1.svg": {"result": False, "msg": "Could not fix"}})
            return {"success": True, "data": {}, "results": {}}

        return side_effect

    def test_fix_nested_progress_callback(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "path/1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                side_effect=self._make_fix_nested_side_effect(),
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={"success": True, "results": {}, "data": {"files": {}}},
            ),
        ):
            worker.args["upload"] = False
            result = worker.process()

        assert "Analyzing" in result.stages.nested.message
        assert result.files_processed["File1.svg"].steps.nested.msg == "Could not fix"
        assert result.files_processed["File1.svg"].status == "failed"

    def test_inject_run_after_with_empty_file_data(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "path/1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={
                    "success": True,
                    "results": {},
                    "data": {"files": {}},
                },
            ),
        ):
            worker.args["upload"] = False
            result = worker.process()

        assert result.files_processed["File1.svg"].steps.inject.msg == "Injection failed or skipped"
        assert result.files_processed["File1.svg"].status == "failed"

    def test_inject_run_after_with_failed_result(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "path/1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={
                    "success": True,
                    "results": {"File1.svg": {"result": False, "msg": "Inject error"}},
                    "data": {"files": {}},
                },
            ),
        ):
            worker.args["upload"] = False
            result = worker.process()

        assert result.files_processed["File1.svg"].steps.inject.result is False
        assert result.files_processed["File1.svg"].steps.inject.msg == "Inject error"
        assert result.files_processed["File1.svg"].status == "failed"
        assert result.files_processed["File1.svg"].error == "Inject error"

    def test_upload_run_after_updates_files_processed(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={
                    "success": True,
                    "main_title": "Main.svg",
                    "titles": ["File1.svg", "File2.svg", "File3.svg"],
                },
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={
                    "success": True,
                    "files_dict": {"File1.svg": "p1", "File2.svg": "p2", "File3.svg": "p3"},
                },
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={
                    "success": True,
                    "results": {},
                    "data": {
                        "files": {
                            "File1.svg": {"file_path": "p1/injected"},
                            "File2.svg": {"file_path": "p2/injected"},
                            "File3.svg": {"file_path": "p3/injected"},
                        }
                    },
                },
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_step",
                return_value={
                    "success": True,
                    "summary": {"uploaded": 1, "failed": 1, "no_changes": 1},
                    "errors": [],
                    "results": {
                        "File1.svg": {"result": True, "msg": "Uploaded"},
                        "File2.svg": {"result": False, "msg": "Upload error"},
                        "File3.svg": {"result": None, "msg": "No changes"},
                    },
                },
            ),
        ):
            result = worker.process()

        assert result.files_processed["File1.svg"].status == "completed"
        assert result.files_processed["File1.svg"].steps.upload.msg == "Uploaded"
        assert result.files_processed["File2.svg"].status == "failed"
        assert result.files_processed["File2.svg"].error == "Upload error"
        assert result.files_processed["File3.svg"].status == "completed"

    def test_upload_run_after_pending_becomes_completed(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "p1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={
                    "success": True,
                    "results": {"File1.svg": {"result": True, "msg": "Injected 1 languages"}},
                    "data": {"files": {}},
                },
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_step",
                return_value={
                    "success": True,
                    "summary": {"uploaded": 0, "failed": 0, "no_changes": 0},
                    "errors": [],
                    "results": {},
                },
            ),
        ):
            result = worker.process()

        assert result.files_processed["File1.svg"].status == "completed"

    def test_upload_progress_callback(self, worker, mock_clients, tmp_path):
        worker.output_dir = tmp_path

        def upload_side_effect(*args, **kwargs):
            cb = kwargs.get("progress_callback")
            if cb:
                cb(10)
            return {
                "success": True,
                "summary": {"uploaded": 1, "failed": 0, "no_changes": 0},
                "errors": [],
                "results": {"File1.svg": {"result": True, "msg": "OK"}},
            }

        with (
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
                return_value={"success": True, "text": "some text"},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
                return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
                return_value={"success": True, "translations": {"new": {"en": "Text"}}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_step",
                return_value={"success": True, "files_dict": {"File1.svg": "p1"}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_step",
                return_value={"success": True, "data": {}, "results": {}},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step",
                return_value={
                    "success": True,
                    "results": {},
                    "data": {"files": {"File1.svg": {"file_path": "p1/injected"}}},
                },
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_step",
                side_effect=upload_side_effect,
            ),
        ):
            result = worker.process()

        assert result.stages.upload.status == "Completed"
