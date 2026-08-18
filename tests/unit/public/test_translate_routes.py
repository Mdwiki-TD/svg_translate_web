from __future__ import annotations

import json
import shutil
from unittest.mock import MagicMock

import pytest
from flask import g
from flask.testing import FlaskClient

from src.main_app.api_services.files_service.objects import (
    DownloadAndSaveData,
    FileInfo,
    UploadResult,
)
from src.main_app.public.main_routes.translate_routes import get_session_dir
from src.main_app.services.copysvg_wrapper.mapping import (
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
        "src.main_app.public.auth.decorators.get_current_user",
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

    def test_select_post_redirects_to_edit(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Posting to select endpoint downloads, extracts, and redirects to edit with session_id."""
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
        mapping = ExtractorData(new={"Hello": {}})
        mock_extract = ExtractResult(success=True, mapping=mapping)
        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.extract_from_path",
            lambda path, fast_return_false: mock_extract,
        )

        resp = mock_client.post(
            "/translate/select",
            data={
                "filename": "Example.svg",
                "lang": "ar",
            },
        )
        assert resp.status_code == 302
        assert "/translate/edit?session_id=" in resp.headers["Location"]

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

    def test_edit_get_success(self, mock_client: FlaskClient) -> None:
        """GET edit successfully loads and displays segments from session folder."""
        session_id = "testsession123"
        session_dir = get_session_dir(session_id)

        # Write mock files to session directory
        svg_path = session_dir / "session.svg"
        svg_path.write_text("<svg></svg>", encoding="utf-8")

        session_data = {
            "filename": "Example.svg",
            "lang": "ar",
            "mapping": {
                "new": {
                    "Hello": {"ar": "مرحبا"},
                    "World": {},
                }
            },
        }
        json_path = session_dir / "session.json"
        json_path.write_text(json.dumps(session_data), encoding="utf-8")

        try:
            resp = mock_client.get(f"/translate/edit?session_id={session_id}")
            assert resp.status_code == 200
            assert b"Example.svg" in resp.data
            assert b"Hello" in resp.data
            assert b"\xd9\x85\xd8\xb1\xd8\xad\xd8\xa8\xd8\xa7" in resp.data  # "مرحبا" in UTF-8
            assert b"World" in resp.data
        finally:
            if session_dir.exists():
                shutil.rmtree(session_dir)

    def test_edit_get_invalid_session(self, mock_client: FlaskClient) -> None:
        """GET edit displays dashboard when session doesn't exist."""
        resp = mock_client.get("/translate/edit?session_id=nonexistentsession")
        assert resp.status_code == 302
        assert "/translate/" in resp.headers["Location"]

    def test_save_post_upload_success(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """POST save successfully injects, uploads and redirects to dashboard."""
        session_id = "testsession456"
        session_dir = get_session_dir(session_id)

        # Write mock files to session directory
        svg_path = session_dir / "session.svg"
        svg_path.write_text("<svg></svg>", encoding="utf-8")

        session_data = {
            "filename": "Example.svg",
            "lang": "ar",
            "mapping": {
                "new": {
                    "Hello": {},
                }
            },
        }
        json_path = session_dir / "session.json"
        json_path.write_text(json.dumps(session_data), encoding="utf-8")

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

        try:
            resp = mock_client.post(
                "/translate/save",
                data={
                    "session_id": session_id,
                    "action": "upload",
                    "originals": ["Hello"],
                    "translations": ["مرحبا"],
                },
            )
            assert resp.status_code == 302
            assert "/translate/" in resp.headers["Location"]
            # File should be cleaned up on upload success
            assert not session_dir.exists()
        finally:
            if session_dir.exists():
                shutil.rmtree(session_dir)

    def test_save_post_download_success(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """POST save with action=download successfully injects and sends file."""
        session_id = "testsession789"
        session_dir = get_session_dir(session_id)

        # Write mock files to session directory
        svg_path = session_dir / "session.svg"
        svg_path.write_text("<svg></svg>", encoding="utf-8")

        session_data = {
            "filename": "Example1.svg",
            "lang": "ar",
            "mapping": {
                "new": {
                    "Hello": {},
                }
            },
        }
        json_path = session_dir / "session.json"
        json_path.write_text(json.dumps(session_data), encoding="utf-8")

        # Mock inject_step_one_file to write a mock translated file
        def fake_inject(file_path, translations, output_file, overwrite_translations):
            output_file.write_text("<svg>Translated content</svg>", encoding="utf-8")
            return InjectResult(result=True)

        monkeypatch.setattr(
            "src.main_app.public.main_routes.translate_routes.inject_step_one_file",
            fake_inject,
        )

        try:
            resp = mock_client.post(
                "/translate/save",
                data={
                    "session_id": session_id,
                    "action": "download",
                    "originals": ["Hello"],
                    "translations": ["مرحبا"],
                },
            )
            assert resp.status_code == 200
            assert resp.mimetype == "image/svg+xml"
            assert b"Translated content" in resp.data
        finally:
            if session_dir.exists():
                shutil.rmtree(session_dir)
