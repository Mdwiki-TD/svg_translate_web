from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from flask import Flask, g
from flask.testing import FlaskClient

from src.main_app.api_services.files_service.objects import (
    DownloadAndSaveData,
    FileInfo,
    UploadResult,
)
from src.main_app.shared.copysvg_wrapper.mapping import (
    ExtractorData,
    ExtractResult,
    InjectResult,
)


class MockUser:
    def __init__(
        self,
        username: str = "alice",
        user_id: int = 1,
        access_token: bytes = b"token",
        access_secret: bytes = b"secret",
    ) -> None:
        self.username = username
        self.user_id = user_id
        self.access_token = access_token
        self.access_secret = access_secret
        self.is_active_admin = False


@pytest.fixture(autouse=True)
def mock_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_user = MockUser(username="alice")

    def fake_load_user() -> MockUser:
        g._current_user = mock_user
        return mock_user

    monkeypatch.setattr(
        "src.main_app.public.auth.utils.load_user",
        fake_load_user,
    )


class TestTranslateRoutes:
    def test_dashboard_renders(self, mock_client: FlaskClient) -> None:
        """Dashboard GET request returns form and status 200."""
        resp = mock_client.get("/translate/")
        assert resp.status_code == 200
        assert b"Translate SVG" in resp.data
        assert b"File Name" in resp.data
        assert b"Language Code" in resp.data

    def test_select_post_redirects_to_edit(self, mock_client: FlaskClient) -> None:
        """Posting to select endpoint redirects to edit_get with proper params."""
        resp = mock_client.post(
            "/translate/select",
            data={
                "filename": "Example.svg",
                "lang": "ar",
            },
        )
        assert resp.status_code == 302
        assert "/translate/edit?filename=Example.svg&lang=ar" in resp.headers["Location"]

    def test_select_post_missing_fields(self, mock_client: FlaskClient) -> None:
        """Posting without required fields redirects to dashboard."""
        resp = mock_client.post(
            "/translate/select",
            data={
                "filename": "",
                "lang": "ar",
            },
        )
        assert resp.status_code == 302
        assert "/translate/" in resp.headers["Location"]

    def test_edit_get_success(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """GET edit successfully extracts and displays segments."""
        # Mock get_file_info
        mock_file_info = FileInfo(exists=True)
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.FilesService.get_file_info",
            lambda self, title: mock_file_info,
        )

        # Mock download_and_save
        mock_download = DownloadAndSaveData(result="success", path="/tmp/Example.svg")
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.FilesService.download_and_save",
            lambda self, title, out_dir, overwrite_download: mock_download,
        )

        # Mock extract_from_path
        mapping = ExtractorData(
            new={
                "Hello": {"ar": "مرحبا"},
                "World": {},
            }
        )
        mock_extract = ExtractResult(success=True, mapping=mapping)
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.extract_from_path",
            lambda path, fast_return_false: mock_extract,
        )

        resp = mock_client.get("/translate/edit?filename=Example.svg&lang=ar")
        assert resp.status_code == 200
        assert b"Example.svg" in resp.data
        assert b"Hello" in resp.data
        assert b"\xd9\x85\xd8\xb1\xd8\xad\xd8\xa8\xd8\xa7" in resp.data  # "مرحبا" in UTF-8
        assert b"World" in resp.data

    def test_edit_get_file_not_exist(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """GET edit displays form with error when file doesn't exist."""
        mock_file_info = FileInfo(exists=False)
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.FilesService.get_file_info",
            lambda self, title: mock_file_info,
        )

        resp = mock_client.get("/translate/edit?filename=Nonexistent.svg&lang=ar")
        assert resp.status_code == 200
        assert b"File File:Nonexistent.svg does not exist" in resp.data

    def test_save_post_success(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """POST save successfully injects, uploads and redirects to dashboard."""
        # Mock download_and_save
        mock_download = DownloadAndSaveData(result="success", path="/tmp/Example.svg")
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.FilesService.download_and_save",
            lambda self, title, out_dir, overwrite_download: mock_download,
        )

        # Mock extract_from_path
        mapping = ExtractorData(new={"Hello": {}})
        mock_extract = ExtractResult(success=True, mapping=mapping)
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.extract_from_path",
            lambda path, fast_return_false: mock_extract,
        )

        # Mock inject_step_one_file
        mock_inject = InjectResult(result=True)
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.inject_step_one_file",
            lambda file_path, translations, output_file, overwrite_translations: mock_inject,
        )

        # Mock get_user_site
        mock_site = MagicMock()
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.get_user_site",
            lambda user: mock_site,
        )

        # Mock UploadService.upload_svg
        mock_upload = UploadResult(ok=True)
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.UploadService.upload_svg",
            lambda self, filename, file_path, summary: mock_upload,
        )

        resp = mock_client.post(
            "/translate/save",
            data={
                "filename": "Example.svg",
                "lang": "ar",
                "originals": ["Hello"],
                "translations": ["مرحبا"],
            },
        )
        assert resp.status_code == 302
        assert "/translate/" in resp.headers["Location"]
