"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
    copy_svg_langs_worker_entry,
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



@pytest.fixture
def mock_steps():
    with (
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step") as m_text,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step") as m_titles,
        patch(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step"
        ) as m_trans,
    ):
        yield {
            "text": m_text,
            "titles": m_titles,
            "translations": m_trans,
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
def mock_worker():
    user = {"username": "testuser", "id": 123}
    args = {"title": "File:Test.svg", "upload": True}
    _worker = CopySvgLangsWorker(job_id=1, user=user, args=args)
    _worker._save_progress = MagicMock()
    return _worker


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
        assert result.stages.text.status == "pending"
        assert result.stages.titles.status == "pending"
        assert result.stages.translations.status == "pending"

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

class TestCopySvgLangsWorkerProcess:
    def test_process_no_title(self, mock_worker: CopySvgLangsWorker, mock_clients):
        mock_worker.title = None
        result = mock_worker.process()
        assert result.status == "failed"

    def test_process_success(self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path):
        mock_worker.output_dir = tmp_path

        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]}
        mock_steps["translations"].return_value = {"success": True, "translations": {"new": {"en": "Text"}}}
        result = mock_worker.process()

        # BaseObjectsJobWorker.run sets it to completed, but process() returns current state
        assert result.status == "pending"
    def test_process_stage_fails(self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients):
        mock_steps["text"].return_value = {"success": False, "error": "Extraction failed"}

        result = mock_worker.process()

        assert result.status == "failed"
        assert result.stages.text.status == "failed"
        assert result.stages.text.message == "Extraction failed"

    def test_process_auth_failed(self, mock_worker: CopySvgLangsWorker, mock_clients, tmp_path):
        mock_worker.output_dir = tmp_path
        mock_clients["site"].return_value = None

        result = mock_worker.process()

        assert result.errors[0].get("error") == "No authenticated user site available."

    def test_process_cancelled(self, mock_worker: CopySvgLangsWorker, mock_clients):
        with patch.object(CopySvgLangsWorker, "is_cancelled", return_value=True):
            result = mock_worker.process()
            assert result.stages.text.status == "cancelled"

    def test_compute_output_dir_none(self, mock_worker: CopySvgLangsWorker):
        assert mock_worker._compute_output_dir(None) is None

    def test_save_files_stats_error(self, mock_worker: CopySvgLangsWorker, tmp_path):
        mock_worker.output_dir = tmp_path
        bad_path = tmp_path / "files_stats.json"
        bad_path.mkdir()

        # Should not raise exception
        mock_worker._save_files_stats({"data": "test"})

    def test_save_files_stats_unexpected_exception(self, mock_worker: CopySvgLangsWorker, tmp_path):
        mock_worker.output_dir = tmp_path

        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.json.dump",
            side_effect=RuntimeError("unexpected"),
        ):
            mock_worker._save_files_stats({"key": "value"})
