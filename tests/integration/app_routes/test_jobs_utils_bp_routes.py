"""Integration tests for the admin jobs management routes."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from werkzeug.wrappers import Response

from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.db.services import jobs_service as _sqlalchemy_jobs_service
from src.main_app.extensions import db as _db


class _JobsStore:
    """Adapter bridging old JobsDB API to SQLAlchemy jobs_service functions."""

    def create(self, job_type, username="z"):
        return _sqlalchemy_jobs_service.create_job(job_type, username)

    def list(self, limit=100, job_type=None):
        return _sqlalchemy_jobs_service.list_jobs(limit, job_type)

    def update_status(self, job_id, status, result_file=None, *, job_type):
        return _sqlalchemy_jobs_service.update_job_status(job_id, status, result_file, job_type=job_type)

    def get(self, job_id, job_type):
        return _sqlalchemy_jobs_service.get_job(job_id, job_type)

    def delete(self, job_id, job_type):
        return _sqlalchemy_jobs_service.delete_job(job_id, job_type)

    def cancel(self, job_id, job_type=None):
        return _sqlalchemy_jobs_service.cancel_job_db(job_id, job_type)


@pytest.fixture
def jobs_db():
    return _JobsStore()


@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client paired with a fake jobs jobs_db."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    admin_user = SimpleNamespace(username="admin", is_active_admin=True)

    def fake_current_user() -> SimpleNamespace:
        return admin_user

    monkeypatch.setattr("src.main_app.app_routes.auth.utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admins_required.load_user", fake_current_user)
    monkeypatch.setattr(
        "src.main_app.app_routes.utils.routes_utils._is_admin",
        lambda user: bool(getattr(user, "is_active_admin", False)),
    )

    app = create_app(TestingConfig)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables)
        yield app.test_client()
        _db.session.remove()
        _db.metadata.drop_all(_db.engine, tables=real_tables)


@patch("src.main_app.app_routes.jobs_utils_bp.send_from_directory")
@patch("src.main_app.app_routes.jobs_utils_bp.settings")
def test_serve_download_main_file(mock_settings, mock_send, admin_jobs_client, tmp_path):
    """Test serving a downloaded main file."""

    main_files_path = str(tmp_path / "main_files")
    mock_settings.paths.main_files_path = main_files_path

    mock_response = Response("file_content")
    mock_send.return_value = mock_response

    response = admin_jobs_client.get("/jobs_utils/download_main_files/file/test.svg")
    assert response.status_code == 200

    mock_send.assert_called_once_with(main_files_path, "test.svg")


@patch("src.main_app.app_routes.jobs_utils_bp.create_main_files_zip")
def test_download_all_main_files(mock_create_zip, admin_jobs_client):
    """Test downloading all main files as zip."""

    mock_create_zip.return_value = ("zip_content", 200)

    response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all")
    assert response.status_code == 200

    mock_create_zip.assert_called_once()


@patch("src.main_app.app_routes.jobs_utils_bp.create_main_files_zip")
def test_download_all_main_files_no_zip(mock_create_zip, admin_jobs_client, monkeypatch):
    """Test downloading all main files when zip doesn't exist - should redirect with flash."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.jobs_utils_bp.flash", mock_flash)

    mock_create_zip.return_value = ("Please run a 'Download Main Files' job first", 404)

    response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
    # Should redirect to jobs list page with flash message
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Please run a 'Download Main Files' job first", "warning")

    mock_create_zip.assert_called_once()


@patch("src.main_app.app_routes.jobs_utils_bp.create_main_files_zip")
def test_download_all_main_files_error(mock_create_zip, admin_jobs_client, monkeypatch):
    """Test downloading all main files when zip is corrupted - should redirect with flash."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.jobs_utils_bp.flash", mock_flash)

    mock_create_zip.return_value = ("Zip file is empty or corrupted", 500)

    response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
    # Should redirect to jobs list page with flash message
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Zip file is empty or corrupted", "danger")

    mock_create_zip.assert_called_once()


def test_serve_download_main_file_with_path_traversal_attempt(admin_jobs_client, jobs_db):
    """Test that path traversal is handled by send_from_directory."""

    # send_from_directory should handle path traversal attempts
    with patch("src.main_app.app_routes.jobs_utils_bp.send_from_directory") as mock_send:
        mock_send.return_value = Response("safe response")
        response = admin_jobs_client.get("/jobs_utils/download_main_files/file/../../../etc/passwd")
        assert response.status_code == 404
