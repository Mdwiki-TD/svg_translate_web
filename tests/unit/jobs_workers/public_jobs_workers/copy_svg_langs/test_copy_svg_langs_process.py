"""Unit tests for CopySvgLangsWorker.process and related methods."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import CopySvgLangsWorker


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
    worker = CopySvgLangsWorker(job_id=1, user=user, args=args)
    worker._save_progress = MagicMock()
    return worker


class TestCopySvgLangsWorkerProcess:
    def test_process_no_title(self, worker, mock_clients):
        worker.title = None
        result = worker.process()
        assert result["status"] == "failed"

    def test_process_success(self, worker, mock_steps, mock_clients, tmp_path):
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

        result = worker.process()

        assert (
            result["status"] == "running"
        )  # BaseObjectsJobWorker.run sets it to completed, but process() returns current state
        assert worker.result["stages"]["upload"]["status"] == "Completed"
        assert "upload_result" in result["results_summary"]

    def test_process_stage_fails(self, worker, mock_steps, mock_clients):
        mock_steps["text"].return_value = {"success": False, "error": "Extraction failed"}

        result = worker.process()

        assert result["status"] == "failed"
        assert result["stages"]["text"]["status"] == "Failed"
        assert result["stages"]["text"]["message"] == "Extraction failed"

    def test_process_upload_disabled(self, worker, mock_steps, mock_clients, tmp_path):
        worker.output_dir = tmp_path
        worker.args["upload"] = False

        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": []}
        mock_steps["translations"].return_value = {"success": True, "translations": {}}
        mock_steps["download"].return_value = {"success": True, "files_dict": {}}
        mock_steps["nested"].return_value = {"success": True, "data": {}, "results": {}}
        mock_steps["inject"].return_value = {"success": True, "results": {}, "data": {"files": {}}}

        result = worker.process()

        assert result["stages"]["upload"]["status"] == "Skipped"
        assert result["stages"]["upload"]["message"] == "Upload disabled"

    def test_process_auth_failed(self, worker, mock_steps, mock_clients, tmp_path):
        worker.output_dir = tmp_path
        mock_clients["site"].return_value = None

        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": []}
        mock_steps["translations"].return_value = {"success": True, "translations": {}}
        mock_steps["download"].return_value = {"success": True, "files_dict": {}}
        mock_steps["nested"].return_value = {"success": True, "data": {}, "results": {}}
        mock_steps["inject"].return_value = {"success": True, "results": {}, "data": {"files": {}}}

        result = worker.process()

        assert result["stages"]["upload"]["status"] == "Failed"
        assert result["stages"]["upload"]["message"] == "Authentication failed"

    def test_process_cancelled(self, worker, mock_clients):
        with patch.object(CopySvgLangsWorker, "is_cancelled", return_value=True):
            result = worker.process()
            assert result["stages"]["text"]["status"] == "Cancelled"

    def test_run_stage_exception(self, worker):
        def failing_step():
            raise ValueError("Boom")

        success = worker._run_stage("text", failing_step)
        assert success is False
        assert worker.result["stages"]["text"]["status"] == "Failed"
        assert "Boom" in worker.result["stages"]["text"]["message"]

    def test_compute_output_dir_none(self, worker):
        assert worker._compute_output_dir(None) is None

    def test_log_upload_error(self, worker):
        worker.result["files_processed"] = {"File1.svg": {"status": "pending", "steps": {"upload": {}}}}
        worker.log_upload_error("Some error", False, "Failed")

        assert worker.result["stages"]["upload"]["status"] == "Failed"
        assert worker.result["files_processed"]["File1.svg"]["status"] == "Failed"
        assert worker.result["files_processed"]["File1.svg"]["steps"]["upload"]["msg"] == "Some error"

    def test_save_files_stats_error(self, worker, tmp_path):
        # Provoke error by using a directory as a file path
        worker.output_dir = tmp_path
        bad_path = tmp_path / "files_stats.json"
        bad_path.mkdir()

        # Should not raise exception
        worker._save_files_stats({"data": "test"})
