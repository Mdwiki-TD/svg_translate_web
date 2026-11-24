"""Unit tests for jobs_files_service."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.main_app.database.models.jobs import JobRecord
from src.main_app.io.jobs_files_service import JobFilesService
from src.main_app.jobs_workers.utils import generate_result_file_name


@pytest.fixture
def jobs_path(tmp_path: Path) -> Path:
    """Directory the service is configured to use (not created up front)."""
    return tmp_path / "jobs"


@pytest.fixture
def mock_settings(jobs_path: Path) -> MagicMock:
    """Settings double that is passed directly to ``JobFilesService``."""
    _mock = MagicMock()
    _mock.paths.jobs_path = str(jobs_path)
    return _mock


@pytest.fixture
def service(mock_settings: MagicMock) -> JobFilesService:
    """Service instance bound to the temporary jobs directory."""
    return JobFilesService(settings=mock_settings)


class TestInit:
    """Tests for ``JobFilesService.__init__``."""

    def test_uses_jobs_path_from_settings(self, mock_settings, jobs_path):
        svc = JobFilesService(settings=mock_settings)
        assert svc.settings is mock_settings
        assert svc.jobs_dir == jobs_path

    def test_creates_jobs_directory(self, mock_settings, jobs_path):
        assert not jobs_path.exists()
        JobFilesService(settings=mock_settings)
        assert jobs_path.is_dir()

    def test_base_dir_overrides_settings(self, mock_settings, tmp_path):
        mock_settings.paths.jobs_path = None
        svc = JobFilesService(base_dir=tmp_path, settings=mock_settings)
        assert svc.jobs_dir == tmp_path

    def test_falls_back_to_get_settings(self, mock_settings, jobs_path):
        with patch(
            "src.main_app.io.jobs_files_service.get_settings",
            return_value=mock_settings,
        ) as m_get_settings:
            svc = JobFilesService()
        m_get_settings.assert_called_once_with()
        assert svc.settings is mock_settings
        assert svc.jobs_dir == jobs_path


class TestLoadJobsDir:
    """Tests for ``JobFilesService._load_jobs_dir``."""

    def test_returns_configured_path(self, service, jobs_path):
        assert service._load_jobs_dir() == jobs_path

    def test_creates_nested_directories(self, service, mock_settings, tmp_path):
        nested = tmp_path / "a" / "b" / "jobs"
        mock_settings.paths.jobs_path = str(nested)
        assert service._load_jobs_dir() == nested
        assert nested.is_dir()

    def test_existing_directory_is_accepted(self, service, jobs_path):
        jobs_path.mkdir(parents=True, exist_ok=True)
        assert service._load_jobs_dir() == jobs_path

    @pytest.mark.parametrize("value", [None, ""])
    def test_raises_when_not_configured(self, mock_settings, value):
        mock_settings.paths.jobs_path = value
        with pytest.raises(RuntimeError, match="jobs_path configuration is required"):
            JobFilesService(settings=mock_settings)


class TestSaveData:
    """Tests for ``JobFilesService._save_data``."""

    def test_writes_json(self, tmp_path):
        data = {"status": "ok", "nested": {"total": 5}}
        filepath = tmp_path / "data.json"

        JobFilesService._save_data(data, filepath)

        assert json.loads(filepath.read_text(encoding="utf-8")) == data

    def test_uses_indent(self, tmp_path):
        filepath = tmp_path / "data.json"
        JobFilesService._save_data({"a": 1}, filepath)
        assert filepath.read_text(encoding="utf-8") == '{\n  "a": 1\n}'

    def test_serializes_unknown_types_as_str(self, tmp_path):
        now = datetime(2024, 1, 2, 3, 4, 5)
        filepath = tmp_path / "data.json"

        JobFilesService._save_data({"timestamp": now}, filepath)

        assert json.loads(filepath.read_text(encoding="utf-8")) == {"timestamp": str(now)}

    def test_keeps_non_ascii_characters(self, tmp_path):
        filepath = tmp_path / "data.json"
        JobFilesService._save_data({"name": "مرحبا"}, filepath)
        assert "مرحبا" in filepath.read_text(encoding="utf-8")


class TestSaveResult:
    """Tests for ``JobFilesService.save_result``."""

    def test_saves_by_name(self, service, jobs_path):
        data = {"status": "ok"}

        path = service.save_result("test.json", data)

        assert path == jobs_path / "test.json"
        assert path.exists()
        with open(path, "r") as f:
            assert json.load(f) == data

    def test_overwrites_existing_file(self, service):
        service.save_result("test.json", {"version": 1})
        path = service.save_result("test.json", {"version": 2})

        with open(path, "r") as f:
            assert json.load(f) == {"version": 2}

    def test_saves_job_result_with_generated_name(self, service):
        job = JobRecord(id=1, job_type="collect_templates_data", status="pending")
        result_data = {"job_id": job.id, "summary": {"total": 5, "updated": 3}}

        result_file = generate_result_file_name(job.id, job.job_type)
        path = service.save_result(result_file, result_data)

        assert path is not None
        assert Path(path).exists()
        with open(path, "r") as f:
            saved_data = json.load(f)
        assert saved_data["job_id"] == job.id
        assert saved_data["summary"]["total"] == 5

    def test_saves_result_with_datetime(self, service):
        job = JobRecord(id=1, job_type="test_job", status="pending")
        result_data = {"job_id": job.id, "timestamp": datetime.now(), "data": "test"}

        result_file = generate_result_file_name(job.id, job.job_type)
        path = service.save_result(result_file, result_data)

        assert path.exists()


class TestLoadResultRaw:
    """Tests for ``JobFilesService._load_result``."""

    def test_success(self, service, jobs_path):
        data = {"status": "loaded"}
        (jobs_path / "load.json").write_text(json.dumps(data))

        assert service._load_result("load.json") == data

    def test_does_not_rename_legacy_keys(self, service, jobs_path):
        data = {"pages_errors": 1, "pages_changed": 2}
        (jobs_path / "legacy.json").write_text(json.dumps(data))

        assert service._load_result("legacy.json") == data

    def test_not_found(self, service):
        assert service._load_result("missing.json") is None

    def test_invalid_json_returns_none_and_logs(self, service, jobs_path, caplog):
        (jobs_path / "bad.json").write_text("invalid json")

        with caplog.at_level("ERROR"):
            assert service._load_result("bad.json") is None

        assert "bad.json" in caplog.text

    def test_absolute_path(self, service, tmp_path):
        data = {"job_id": 1}
        result_file = tmp_path / "result.json"
        result_file.write_text(json.dumps(data))

        assert service._load_result(str(result_file)) == data


class TestLoadResult:
    """Tests for ``JobFilesService.load_result``."""

    def test_success(self, service, jobs_path):
        data = {"status": "loaded"}
        (jobs_path / "load.json").write_text(json.dumps(data))

        assert service.load_result("load.json") == data

    def test_not_found(self, service):
        assert service.load_result("missing.json") is None

    def test_nonexistent_absolute_path(self, service):
        assert service.load_result("/nonexistent/file.json") is None

    def test_invalid_json(self, service, jobs_path):
        (jobs_path / "bad.json").write_text("not json")

        assert service.load_result("bad.json") is None

    def test_invalid_json_absolute_path(self, service, tmp_path):
        result_file = tmp_path / "invalid.json"
        result_file.write_text("not valid json")

        assert service.load_result(str(result_file)) is None

    def test_absolute_path(self, service, tmp_path):
        result_file = tmp_path / "result.json"
        result_file.write_text(json.dumps({"job_id": 1, "summary": {"total": 5}}))

        loaded = service.load_result(str(result_file))

        assert loaded is not None
        assert loaded["job_id"] == 1
        assert loaded["summary"]["total"] == 5

    def test_renames_pages_errors_to_pages_failed(self, service, jobs_path):
        (jobs_path / "r.json").write_text(json.dumps({"pages_errors": 3}))

        assert service.load_result("r.json") == {"pages_failed": 3}

    def test_renames_pages_changed_to_pages_updated(self, service, jobs_path):
        (jobs_path / "r.json").write_text(json.dumps({"pages_changed": 4}))

        assert service.load_result("r.json") == {"pages_updated": 4}

    def test_renames_both_legacy_keys(self, service, jobs_path):
        (jobs_path / "r.json").write_text(json.dumps({"pages_errors": 1, "pages_changed": 2, "total": 9}))

        assert service.load_result("r.json") == {"pages_failed": 1, "pages_updated": 2, "total": 9}

    def test_keeps_new_keys_untouched(self, service, jobs_path):
        data = {"pages_failed": 1, "pages_updated": 2}
        (jobs_path / "r.json").write_text(json.dumps(data))

        assert service.load_result("r.json") == data


class TestCreateCancelFile:
    """Tests for ``JobFilesService.create_cancel_file``."""

    def test_success(self, service, jobs_path):
        path = service.create_cancel_file("job.cancel")

        assert path == jobs_path / "job.cancel"
        assert path.exists()
        assert path.read_text() == "cancelled"

    def test_returns_none_on_os_error(self, service, jobs_path):
        # The parent directory does not exist, so opening the file fails.
        assert service.create_cancel_file("missing_dir/job.cancel") is None
        assert not (jobs_path / "missing_dir").exists()


class TestIsCancelFileExist:
    """Tests for ``JobFilesService.is_cancel_file_exist``."""

    def test_true_when_file_exists(self, service, jobs_path):
        (jobs_path / "exist.cancel").touch()

        assert service.is_cancel_file_exist("exist.cancel") is True

    def test_false_when_file_missing(self, service):
        assert service.is_cancel_file_exist("no.cancel") is False

    def test_roundtrip_with_create_cancel_file(self, service):
        assert service.is_cancel_file_exist("job.cancel") is False
        service.create_cancel_file("job.cancel")
        assert service.is_cancel_file_exist("job.cancel") is True

    def test_false_on_os_error(self, service):
        with patch.object(Path, "exists", side_effect=OSError("Access denied")):
            assert service.is_cancel_file_exist("any.cancel") is False
