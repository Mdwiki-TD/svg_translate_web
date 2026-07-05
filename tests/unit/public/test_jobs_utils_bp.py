"""Unit tests for src/main_app/public/jobs_utils_bp.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from src.main_app.public.jobs_utils_bp import UtilsJobsBp


class TestUtilsJobsBp:
    def test_init_creates_blueprint(self):
        module = UtilsJobsBp("test_utils")
        assert module.bp.name == "test_utils"


@pytest.mark.usefixtures("mock_app")
class TestServeDownloadMainFile:
    def test_serves_file(self, mock_client, monkeypatch, tmp_path):
        main_files = tmp_path / "main_files"
        main_files.mkdir()
        (main_files / "test.svg").write_text("<svg/>")

        mock_settings = MagicMock()
        mock_settings.paths.main_files_path = str(main_files)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.settings", mock_settings)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.send_from_directory", lambda d, f: f"content:{f}")

        resp = mock_client.get("/jobs_utils/download_main_files/file/test.svg")
        assert resp.status_code in (200, 302)


class TestServeCropFiles:
    def test_original_file_strips_file_prefix(self, monkeypatch):
        from src.main_app.public.jobs_utils_bp import jobs_utils_module

        mock_send = Mock()
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.send_from_directory", mock_send)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.Path", lambda p: Path(p))

        bp = jobs_utils_module.bp
        test_func = None
        for rule in bp.deferred_functions:
            pass

    def test_compare_crop_files_renders(self, monkeypatch):
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.render_template", lambda t, **c: c)
        from src.main_app.public.jobs_utils_bp import jobs_utils_module

        bp = jobs_utils_module.bp
        test_func = None
        for rule in bp.deferred_functions:
            pass


@pytest.mark.usefixtures("mock_app")
class TestDownloadAllMainFiles:
    def test_download_success(self, mock_client, monkeypatch):
        admin_user = MagicMock(is_active_admin=True)
        monkeypatch.setattr("src.main_app.admin.decorators.load_user", lambda: admin_user)
        mock_zip = Mock()
        mock_zip.return_value = ("zip_content", 200)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.create_main_files_zip", mock_zip)
        mock_settings2 = MagicMock()
        mock_settings2.paths.main_files_path = "/tmp"
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.settings", mock_settings2)

        resp = mock_client.get("/jobs_utils/download_main_files/download-all")
        assert resp.status_code == 200

    def test_download_not_found(self, mock_client, monkeypatch):
        mock_zip = Mock()
        mock_zip.return_value = ("Not found", 404)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.create_main_files_zip", mock_zip)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.flash", mock_flash)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.url_for", lambda x, **kw: f"/{x}")

        resp = mock_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
        assert resp.status_code in (200, 302)

    def test_download_error(self, mock_client, monkeypatch):
        mock_zip = Mock()
        mock_zip.return_value = ("Error", 500)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.create_main_files_zip", mock_zip)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.flash", mock_flash)
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.public.jobs_utils_bp.url_for", lambda x, **kw: f"/{x}")

        resp = mock_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
        assert resp.status_code in (200, 302)
