"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

import threading
from pathlib import Path
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
        patch("src.main_app.jobs_workers.base_worker_object.get_user_site") as m_site,
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


@pytest.fixture
def mock_process_one_deps():
    with (
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_svg_file") as m_dl,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.detect_nested_tags") as m_detect,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.fix_nested_tags") as m_fix,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.verify_fix") as m_verify,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step_one_file") as m_inject,
        patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_fixed_svg") as m_upload,
    ):
        yield {
            "download": m_dl,
            "detect": m_detect,
            "fix": m_fix,
            "verify": m_verify,
            "inject": m_inject,
            "upload": m_upload,
        }


class TestCopySvgLangsWorkerInjectStepFile:
    def test_no_file_path(self, mock_worker: CopySvgLangsWorker):
        step_result, new_path = mock_worker.inject_step_file("")

        assert step_result.result is False
        assert step_result.msg == "No file path found"
        assert new_path is None

    def test_inject_result_none(self, mock_worker: CopySvgLangsWorker, monkeypatch, tmp_path):
        mock_worker.output_dir = tmp_path
        mock_inject = MagicMock(return_value=MagicMock(result=None, msg="No changes"))
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step_one_file",
            mock_inject,
        )

        step_result, new_path = mock_worker.inject_step_file(str(tmp_path / "test.svg"))

        assert step_result.result is None
        assert step_result.msg == "No changes"
        assert new_path is None

    def test_inject_result_false(self, mock_worker: CopySvgLangsWorker, monkeypatch, tmp_path):
        mock_worker.output_dir = tmp_path
        mock_inject = MagicMock(return_value=MagicMock(result=False, msg="Nested tspan error"))
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step_one_file",
            mock_inject,
        )

        step_result, new_path = mock_worker.inject_step_file(str(tmp_path / "test.svg"))

        assert step_result.result is False
        assert step_result.msg == "Nested tspan error"
        assert new_path is None

    def test_inject_result_true(self, mock_worker: CopySvgLangsWorker, monkeypatch, tmp_path):
        mock_worker.output_dir = tmp_path
        mock_inject = MagicMock(
            return_value=MagicMock(result=True, msg="2 languages injected", new_languages=2, updated_translations=1)
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step_one_file",
            mock_inject,
        )

        file_name = "test.svg"
        file_path = tmp_path / file_name
        file_path.write_text("")
        step_result, new_path = mock_worker.inject_step_file(str(file_path))

        assert step_result.result is True
        assert step_result.msg == "2 languages injected"
        assert step_result.details == {"new_languages": 2, "updated_translations": 1}
        assert new_path == tmp_path / "translated" / file_name


class TestCopySvgLangsWorkerProcessOne:
    def test_download_exception(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps):
        mock_process_one_deps["download"].side_effect = ValueError("Network error")
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.steps.download.msg == "Error downloading"
        assert title_info.status == "failed"

    def test_download_not_ok(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps):
        mock_process_one_deps["download"].return_value = {"ok": False}
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.status == "failed"

    def test_download_no_file_path(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps):
        mock_process_one_deps["download"].return_value = {"ok": True, "path": ""}
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.status == "failed"

    def test_no_nested_tags(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=0)
        mock_process_one_deps["inject"].return_value = MagicMock(result=None, msg="No changes")
        from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import FilesProcessedItem

        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert title_info.steps.nested.result is None
        assert title_info.steps.nested.msg == "No nested tags found"

    def test_fix_nested_tags_fails(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=2)
        mock_process_one_deps["fix"].return_value = False
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False
        assert title_info.steps.nested.result is False
        assert title_info.status == "failed"
        assert title_info.steps.inject.msg == "skipped"
        assert title_info.steps.upload.msg == "skipped"

    def test_verify_fix_zero(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=2)
        mock_process_one_deps["fix"].return_value = True
        mock_process_one_deps["verify"].return_value = MagicMock(fixed=0)
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False
        assert title_info.steps.nested.result is False
        assert title_info.status == "failed"

    def test_inject_success_uploads(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=0)
        mock_process_one_deps["inject"].return_value = MagicMock(
            result=True, msg="ok", new_languages=1, updated_translations=0
        )
        mock_process_one_deps["inject"].return_value.details = {"new_languages": 1, "updated_translations": 0}
        mock_process_one_deps["upload"].return_value = {"ok": True, "error": "", "msg": "uploaded"}
        mock_worker.main_title = "Main.svg"
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is True
        assert title_info.steps.upload.result is True
        assert title_info.status == "success"

    def test_inject_none_no_nested_tags(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=0)
        mock_process_one_deps["inject"].return_value = MagicMock(result=None, msg="No changes")
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False

    def test_inject_false_no_nested_tags(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=0)
        mock_process_one_deps["inject"].return_value = MagicMock(result=False, msg="Failed")
        title_info = MagicMock(title="File:Test.svg", steps=MagicMock(inject=MagicMock(result=False)))

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False

    def test_inject_false_but_nested_fixed(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=2)
        mock_process_one_deps["fix"].return_value = True
        mock_process_one_deps["verify"].return_value = MagicMock(fixed=2)
        mock_process_one_deps["inject"].return_value = MagicMock(result=False, msg="Failed")
        mock_process_one_deps["upload"].return_value = {"ok": True, "msg": "uploaded", "error": ""}
        from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import FilesProcessedItem

        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        # nested step not updated on success (stays default)
        assert title_info.steps.nested.result is True
        assert title_info.steps.nested.msg == "Fixed 2 nested tag(s)"
        assert title_info.steps.inject.result is False
        assert title_info.steps.inject.msg == "Failed"
        assert result is True

    def test_upload_disabled(self, mock_worker: CopySvgLangsWorker, mock_process_one_deps, tmp_path):
        mock_worker.args = {"upload": False}
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_process_one_deps["download"].return_value = {"ok": True, "path": str(dl_path)}
        mock_process_one_deps["detect"].return_value = MagicMock(count=0)
        mock_process_one_deps["inject"].return_value = MagicMock(
            result=True, msg="ok", new_languages=1, updated_translations=0
        )
        mock_process_one_deps["inject"].return_value.details = {"new_languages": 1, "updated_translations": 0}
        mock_worker.main_title = "Main.svg"
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._process_one_item("File:Test.svg", title_info)

        assert result is False
        assert title_info.steps.upload.result is None
        assert title_info.steps.upload.msg == "skipped"
        assert "Upload disabled" in title_info.steps.upload.details["error"]
        assert title_info.status == "skipped"


class TestCopySvgLangsWorkerUploadStep:
    def test_upload_disabled(self, mock_worker: CopySvgLangsWorker):
        mock_worker.args = {"upload": False}
        title_info = MagicMock()

        result = mock_worker._upload_step(title_info, "summary", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.result is None
        assert title_info.steps.upload.msg == "skipped"
        assert title_info.status == "skipped"

    def test_upload_limit_reached(self, mock_worker: CopySvgLangsWorker):
        mock_worker.args = {"upload": True}
        mock_worker.upload_limit = 5
        mock_worker.upload_done = 5
        title_info = MagicMock()

        result = mock_worker._upload_step(title_info, "summary", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.msg == "skipped"
        assert "Upload limit reached" in title_info.steps.upload.details["error"]
        assert title_info.status == "skipped"

    def test_upload_success(self, mock_worker: CopySvgLangsWorker, monkeypatch):
        mock_worker.args = {"upload": True}
        mock_worker.upload_limit = 5
        mock_worker.upload_done = 0
        mock_worker.site = MagicMock()
        mock_upload = MagicMock(return_value={"ok": True, "error": "", "msg": "uploaded"})
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_fixed_svg",
            mock_upload,
        )
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._upload_step(title_info, "Adding translations", Path("test.svg"))

        assert result is True
        assert title_info.steps.upload.result is True
        assert title_info.steps.upload.msg == "File Successfully uploaded."
        assert title_info.status == "success"
        assert mock_worker.upload_done == 1

    def test_upload_skipped(self, mock_worker: CopySvgLangsWorker, monkeypatch):
        mock_worker.args = {"upload": True}
        mock_worker.site = MagicMock()
        mock_upload = MagicMock(
            return_value={"ok": None, "error": "skipped", "msg": "File exists", "error_details": ""}
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_fixed_svg",
            mock_upload,
        )
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._upload_step(title_info, "Adding translations", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.result is None
        assert title_info.steps.upload.msg == "File exists"

    def test_upload_failure(self, mock_worker: CopySvgLangsWorker, monkeypatch):
        mock_worker.args = {"upload": True}
        mock_worker.site = MagicMock()
        mock_upload = MagicMock(
            return_value={"ok": False, "error": "Upload failed", "msg": "error", "error_details": "details"}
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_fixed_svg",
            mock_upload,
        )
        title_info = MagicMock(title="File:Test.svg")

        result = mock_worker._upload_step(title_info, "Adding translations", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.result is False
        assert title_info.steps.upload.msg == "Upload failed."
        assert title_info.error == "Upload failed"


class TestCopySvgLangsWorkerLimits:
    def test_apply_limits_applied(self, mock_worker: CopySvgLangsWorker):
        mock_worker.limit_items = 2
        titles = ["a.svg", "b.svg", "c.svg", "d.svg"]

        result = mock_worker._apply_limits(titles)

        assert len(result) == 2
        assert result == ["a.svg", "b.svg"]

    def test_apply_limits_no_limit(self, mock_worker: CopySvgLangsWorker):
        mock_worker.limit_items = 0
        titles = ["a.svg", "b.svg", "c.svg"]

        result = mock_worker._apply_limits(titles)

        assert len(result) == 3

    def test_apply_limits_below_limit(self, mock_worker: CopySvgLangsWorker):
        mock_worker.limit_items = 5
        titles = ["a.svg"]

        result = mock_worker._apply_limits(titles)

        assert len(result) == 1


class TestCopySvgLangsWorkerProcessAdvanced:
    def test_process_titles_fails(self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients):
        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": False, "error": "Title extraction failed"}

        result = mock_worker.process()

        assert result.status == "failed"
        assert result.stages.titles.status == "failed"
        assert result.stages.titles.message == "Title extraction failed"

    def test_process_translations_fails(self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients):
        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]}
        mock_steps["translations"].return_value = {"success": False, "error": "Translation extraction failed"}

        result = mock_worker.process()

        assert result.status == "failed"
        assert result.stages.translations.status == "failed"

    def test_process_cancelled_during_loop(self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path):
        mock_worker.output_dir = tmp_path
        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]}
        mock_steps["translations"].return_value = {"success": True, "translations": {"new": {"en": "Text"}}}

        with (
            patch.object(CopySvgLangsWorker, "is_cancelled", side_effect=[False, False, True]),
            patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_svg_file") as m_dl,
            patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.detect_nested_tags") as m_detect,
        ):
            m_dl.return_value = {"ok": True, "path": str(tmp_path / "test.svg")}
            m_detect.return_value = MagicMock(count=0)
            result = mock_worker.process()

        assert result.stages.processfiles.status == "cancelled"

    def test_process_periodic_cancel(self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path):
        mock_worker.output_dir = tmp_path
        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {
            "success": True,
            "main_title": "Main.svg",
            "titles": ["File1.svg", "File2.svg"],
        }
        mock_steps["translations"].return_value = {"success": True, "translations": {"new": {"en": "Text"}}}

        with (
            patch.object(CopySvgLangsWorker, "is_cancelled", return_value=False),
            patch.object(CopySvgLangsWorker, "check_cancel_db_periodic", return_value=True),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_svg_file",
                return_value={"ok": True, "path": str(tmp_path / "test.svg")},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.detect_nested_tags",
                return_value=MagicMock(count=0),
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step_one_file",
                return_value=MagicMock(result=True, msg="ok", new_languages=0, updated_translations=0),
            ) as m_inject,
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.upload_fixed_svg",
                return_value={"ok": True, "error": "", "msg": "uploaded"},
            ),
        ):
            m_inject.return_value.details = {"new_languages": 0, "updated_translations": 0}
            result = mock_worker.process()

        # periodic check breaks loop early - only first file processed
        assert len(result.files_success) == 1
        assert len(result.files_processed) == 0

    def test_process_multiple_files_progress_save(
        self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path
    ):
        mock_worker.output_dir = tmp_path
        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {
            "success": True,
            "main_title": "Main.svg",
            "titles": ["F1.svg", "F2.svg", "F3.svg"],
        }
        mock_steps["translations"].return_value = {"success": True, "translations": {"new": {"en": "Text"}}}

        with (
            patch.object(CopySvgLangsWorker, "is_cancelled", return_value=False),
            patch.object(CopySvgLangsWorker, "check_cancel_db_periodic", return_value=False),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_svg_file",
                return_value={"ok": True, "path": str(tmp_path / "test.svg")},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.detect_nested_tags",
                return_value=MagicMock(count=0),
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step_one_file",
                return_value=MagicMock(result=None, msg="No changes"),
            ),
        ):
            result = mock_worker.process()

        assert result.stages.processfiles.status == "completed"

    def test_title_info_status_normalized(self, mock_worker: CopySvgLangsWorker, mock_steps, mock_clients, tmp_path):
        mock_worker.output_dir = tmp_path
        mock_steps["text"].return_value = {"success": True, "text": "some text"}
        mock_steps["titles"].return_value = {"success": True, "main_title": "Main.svg", "titles": ["F1.svg"]}
        mock_steps["translations"].return_value = {"success": True, "translations": {"new": {"en": "Text"}}}

        with (
            patch.object(CopySvgLangsWorker, "is_cancelled", return_value=False),
            patch.object(CopySvgLangsWorker, "check_cancel_db_periodic", return_value=False),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.download_svg_file",
                return_value={"ok": True, "path": str(tmp_path / "test.svg")},
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.detect_nested_tags",
                return_value=MagicMock(count=0),
            ),
            patch(
                "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.inject_step_one_file",
                return_value=MagicMock(result=None, msg="No changes"),
            ),
        ):
            result = mock_worker.process()

        assert len(result.files_processed) == 1
        assert result.files_processed[0].status in ["completed", "failed"]


class TestCopySvgLangsWorkerStageMethods:
    def test_extract_titles_step_cancelled(self, mock_worker: CopySvgLangsWorker):
        mock_worker.text = "some text"
        with patch.object(CopySvgLangsWorker, "is_cancelled", return_value=True):
            result = mock_worker._extract_titles_step()

        assert result is False
        assert mock_worker.result.stages.titles.status == "cancelled"

    def test_extract_titles_step_exception(self, mock_worker: CopySvgLangsWorker, monkeypatch):
        mock_worker.text = "some text"
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
            MagicMock(side_effect=ValueError("bad data")),
        )

        result = mock_worker._extract_titles_step()

        assert result is False
        assert mock_worker.result.stages.titles.status == "failed"
        assert mock_worker.result.status == "failed"

    def test_extract_titles_step_failed(self, mock_worker: CopySvgLangsWorker, monkeypatch):
        mock_worker.text = "some text"
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
            MagicMock(return_value={"success": False, "error": "No titles found"}),
        )

        result = mock_worker._extract_titles_step()

        assert result is False
        assert mock_worker.result.stages.titles.status == "failed"
        assert mock_worker.result.stages.titles.message == "No titles found"

    def test_extract_titles_step_message_from_result(self, mock_worker: CopySvgLangsWorker, monkeypatch):
        mock_worker.text = "some text"
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step",
            MagicMock(return_value={"success": False, "error": "error", "message": "No titles"}),
        )

        mock_worker._extract_titles_step()

        assert mock_worker.result.stages.titles.message == "error"

    def test_extract_translations_step_exception(self, mock_worker: CopySvgLangsWorker, monkeypatch, tmp_path):
        mock_worker.main_title = "Main.svg"
        mock_worker.output_dir = tmp_path
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
            MagicMock(side_effect=RuntimeError("DB error")),
        )

        result = mock_worker._extract_translations_step()

        assert result is False
        assert mock_worker.result.stages.translations.status == "failed"
        assert mock_worker.result.status == "failed"

    def test_extract_translations_step_failed(self, mock_worker: CopySvgLangsWorker, monkeypatch, tmp_path):
        mock_worker.main_title = "Main.svg"
        mock_worker.output_dir = tmp_path
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_translations_step",
            MagicMock(return_value={"success": False, "error": "No translations"}),
        )

        result = mock_worker._extract_translations_step()

        assert result is False
        assert mock_worker.result.stages.translations.status == "failed"

    def test_extract_text_step_exception(self, mock_worker: CopySvgLangsWorker, monkeypatch):
        mock_worker.title = "File:Test.svg"
        mock_worker.site = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step",
            MagicMock(side_effect=ValueError("connection error")),
        )

        result = mock_worker._extract_text_step()

        assert result is False
        assert mock_worker.result.stages.text.status == "failed"
        assert mock_worker.result.status == "failed"


class TestCopySvgLangsWorkerComputeOutputDir:
    def test_compute_output_dir_none(self, mock_worker: CopySvgLangsWorker):
        assert mock_worker._compute_output_dir(None) is None

    def test_compute_output_dir_creates_dirs(self, mock_worker: CopySvgLangsWorker, tmp_path):
        with patch.object(Path, "mkdir") as mock_mkdir:
            mock_worker._compute_output_dir("File:Test File.svg")

            assert mock_mkdir.call_count == 3
