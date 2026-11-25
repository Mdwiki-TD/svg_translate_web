"""Unit tests for jobs_files_service."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from src.main_app.database.models.jobs import JobRecord
from src.main_app.io.jobs_files_service import JobFilesService
from src.main_app.jobs_workers.utils import generate_result_file_name


@pytest.fixture
def jobs_path(tmp_path: Path) -> Path:
    """Directory the service is configured to use (not created up front)."""
    return tmp_path / "jobs"


@pytest.fixture
def service(jobs_path: Path) -> JobFilesService:
    """Service instance bound to the temporary jobs directory."""
    return JobFilesService(jobs_dir=jobs_path)


@pytest.fixture
def make_json_file(jobs_path: Path, tmp_path: Path) -> Callable[[str, object, bool, bool], str]:
    """Factory creating a JSON or raw text file and returning its target path string."""

    def _factory(
        filename: str,
        content: object,
        *,
        raw_text: bool = False,
        absolute: bool = False,
    ) -> str:
        target_dir = tmp_path if absolute else jobs_path
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename
        payload = content if raw_text else json.dumps(content)
        file_path.write_text(str(payload), encoding="utf-8")
        return str(file_path) if absolute else filename

    return _factory  # pyright: ignore[reportReturnType]


class TestInit:
    """Tests for ``JobFilesService.__init__``."""

    def test_sets_jobs_dir_and_creates_directory(self, jobs_path: Path):
        # Ensure the directory does not exist before initializing the service.
        assert not jobs_path.exists()

        svc = JobFilesService(jobs_dir=jobs_path)

        assert svc.jobs_dir == jobs_path
        assert jobs_path.is_dir()

    def test_raises_when_jobs_dir_is_none(self):
        with pytest.raises(
            RuntimeError,
            match="jobs_path configuration is required for job result storage",
        ):
            JobFilesService(jobs_dir=None)


class TestSaveData:
    """Tests for ``JobFilesService._save_data``."""

    def test_writes_json(self, tmp_path: Path):
        data = {"status": "ok", "nested": {"total": 5}}
        filepath = tmp_path / "data.json"

        JobFilesService._save_data(data, filepath)

        assert json.loads(filepath.read_text(encoding="utf-8")) == data

    def test_uses_indent(self, tmp_path: Path):
        filepath = tmp_path / "data.json"
        JobFilesService._save_data({"a": 1}, filepath)
        assert filepath.read_text(encoding="utf-8") == '{\n  "a": 1\n}'

    def test_serializes_unknown_types_as_str(self, tmp_path: Path):
        now = datetime(2024, 1, 2, 3, 4, 5)
        filepath = tmp_path / "data.json"

        JobFilesService._save_data({"timestamp": now}, filepath)

        assert json.loads(filepath.read_text(encoding="utf-8")) == {"timestamp": str(now)}

    def test_keeps_non_ascii_characters(self, tmp_path: Path):
        filepath = tmp_path / "data.json"
        JobFilesService._save_data({"name": "مرحبا"}, filepath)
        assert "مرحبا" in filepath.read_text(encoding="utf-8")


class TestSaveResult:
    """Tests for ``JobFilesService.save_result``."""

    def test_saves_by_name(self, service: JobFilesService, jobs_path: Path):
        data = {"status": "ok"}

        path = service.save_result("test.json", data)

        assert path == jobs_path / "test.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == data

    def test_overwrites_existing_file(self, service: JobFilesService):
        service.save_result("test.json", {"version": 1})
        path = service.save_result("test.json", {"version": 2})

        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == {"version": 2}

    def test_saves_job_result_with_generated_name(self, service: JobFilesService):
        job = JobRecord(id=1, job_type="collect_templates_data", status="pending")
        result_data = {"job_id": job.id, "summary": {"total": 5, "updated": 3}}

        result_file = generate_result_file_name(job.id, job.job_type)
        path = service.save_result(result_file, result_data)

        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["job_id"] == job.id
        assert saved_data["summary"]["total"] == 5

    def test_saves_result_with_datetime(self, service: JobFilesService):
        job = JobRecord(id=1, job_type="test_job", status="pending")
        result_data = {"job_id": job.id, "timestamp": datetime.now(), "data": "test"}

        result_file = generate_result_file_name(job.id, job.job_type)
        path = service.save_result(result_file, result_data)

        assert path.exists()


class TestLoadResultRaw:
    """Tests for ``JobFilesService._load_result``."""

    def test_success(self, service: JobFilesService, make_json_file):
        data = {"status": "loaded"}
        ref = make_json_file("load.json", data)

        assert service._load_result(ref) == data

    def test_does_not_rename_legacy_keys(self, service: JobFilesService, make_json_file):
        data = {"pages_errors": 1, "pages_changed": 2}
        ref = make_json_file("legacy.json", data)

        assert service._load_result(ref) == data

    def test_not_found_logs_warning_and_returns_none(self, service: JobFilesService, caplog):
        with caplog.at_level("WARNING"):
            assert service._load_result("missing.json") is None

        assert "missing.json" in caplog.text

    def test_invalid_json_returns_none_and_logs(self, service: JobFilesService, make_json_file, caplog):
        ref = make_json_file("bad.json", "invalid json", raw_text=True)

        with caplog.at_level("ERROR"):
            assert service._load_result(ref) is None

        assert "bad.json" in caplog.text

    def test_absolute_path(self, service: JobFilesService, make_json_file):
        data = {"job_id": 1}
        ref = make_json_file("result.json", data, absolute=True)

        assert service._load_result(ref) == data


class TestLoadResult:
    """Tests for ``JobFilesService.load_result``."""

    def test_success(self, service: JobFilesService, make_json_file):
        data = {"status": "loaded"}
        ref = make_json_file("load.json", data)

        assert service.load_result(ref) == data

    def test_not_found(self, service: JobFilesService):
        assert service.load_result("missing.json") is None

    def test_nonexistent_absolute_path(self, service: JobFilesService):
        assert service.load_result("/nonexistent/file.json") is None

    def test_invalid_json(self, service: JobFilesService, make_json_file):
        ref = make_json_file("bad.json", "not json", raw_text=True)

        assert service.load_result(ref) is None

    def test_invalid_json_absolute_path(self, service: JobFilesService, make_json_file):
        ref = make_json_file("invalid.json", "not valid json", raw_text=True, absolute=True)

        assert service.load_result(ref) is None

    def test_absolute_path(self, service: JobFilesService, make_json_file):
        data = {"job_id": 1, "summary": {"total": 5}}
        ref = make_json_file("result.json", data, absolute=True)

        loaded = service.load_result(ref)

        assert loaded is not None
        assert loaded["job_id"] == 1
        assert loaded["summary"]["total"] == 5

    def test_renames_pages_errors_to_pages_failed(self, service: JobFilesService, make_json_file):
        ref = make_json_file("r.json", {"pages_errors": 3})

        assert service.load_result(ref) == {"pages_failed": 3}

    def test_renames_pages_changed_to_pages_updated(self, service: JobFilesService, make_json_file):
        ref = make_json_file("r.json", {"pages_changed": 4})

        assert service.load_result(ref) == {"pages_updated": 4}

    def test_renames_both_legacy_keys(self, service: JobFilesService, make_json_file):
        ref = make_json_file("r.json", {"pages_errors": 1, "pages_changed": 2, "total": 9})

        assert service.load_result(ref) == {
            "pages_failed": 1,
            "pages_updated": 2,
            "total": 9,
        }

    def test_keeps_new_keys_untouched(self, service: JobFilesService, make_json_file):
        data = {"pages_failed": 1, "pages_updated": 2}
        ref = make_json_file("r.json", data)

        assert service.load_result(ref) == data


class TestCreateCancelFile:
    """Tests for ``JobFilesService.create_cancel_file``."""

    def test_success(self, service: JobFilesService, jobs_path: Path):
        path = service.create_cancel_file("job.cancel")

        assert path == jobs_path / "job.cancel"
        assert path.exists()
        assert path.read_text(encoding="utf-8") == "cancelled"

    def test_returns_none_on_os_error(self, service: JobFilesService, jobs_path: Path):
        # The parent directory does not exist, so opening the file fails.
        assert service.create_cancel_file("missing_dir/job.cancel") is None
        assert not (jobs_path / "missing_dir").exists()


class TestIsCancelFileExist:
    """Tests for ``JobFilesService.is_cancel_file_exist``."""

    def test_true_when_file_exists(self, service: JobFilesService, jobs_path: Path):
        (jobs_path / "exist.cancel").touch()

        assert service.is_cancel_file_exist("exist.cancel") is True

    def test_false_when_file_missing(self, service: JobFilesService):
        assert service.is_cancel_file_exist("no.cancel") is False

    def test_roundtrip_with_create_cancel_file(self, service: JobFilesService):
        assert service.is_cancel_file_exist("job.cancel") is False
        service.create_cancel_file("job.cancel")
        assert service.is_cancel_file_exist("job.cancel") is True

    def test_false_on_os_error(self, service: JobFilesService):
        with patch.object(Path, "exists", side_effect=OSError("Access denied")):
            assert service.is_cancel_file_exist("any.cancel") is False
