"""Integration tests for the interactive translate routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.shared.copysvg_wrapper.mapping import ExtractorData
from src.main_app.shared.copysvg_wrapper.translate_session import TranslateSession


@pytest.fixture(autouse=True)
def setup_tests(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Mock external services and use tmp_path for sessions."""
    # Mock file info (file exists on Commons)
    mock_info = MagicMock()
    mock_info.exists = True
    mocker.patch(
        "src.main_app.public.main_routes.translate_routes.FilesService.get_file_info",
        return_value=mock_info,
    )

    # Point sessions to tmp_path
    monkeypatch.setattr(
        "src.main_app.public.main_routes.translate_routes._sessions_base_dir",
        lambda: tmp_path,
    )


@pytest.fixture
def sample_mapping() -> ExtractorData:
    return ExtractorData(
        new={
            "Hello": {"ar": "مرحبا", "fr": "Bonjour"},
            "Goodbye": {"fr": "Au revoir"},
        }
    )


@pytest.fixture
def mock_extract(monkeypatch: pytest.MonkeyPatch, sample_mapping: ExtractorData):
    """Mock the extract step to return sample data."""

    def fake_extract(path, fast_return_false=False):
        from src.main_app.shared.copysvg_wrapper.mapping import ExtractResult

        return ExtractResult(
            success=True,
            message="Loaded 2 translations",
            error=None,
            translations=sample_mapping.to_json(),
            mapping=sample_mapping,
        )

    monkeypatch.setattr(
        "src.main_app.public.main_routes.translate_routes.extract_from_path",
        fake_extract,
    )


@pytest.fixture
def mock_download(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Mock the download step to create a dummy SVG file."""

    def fake_download(*args, **kwargs):
        out_dir = kwargs.get("out_dir")
        title = kwargs.get("title", "Test.svg")
        svg_path = Path(out_dir) / title
        svg_path.write_text("<svg><text>Hello</text></svg>")
        return DownloadAndSaveData(result="success", path=str(svg_path))

    monkeypatch.setattr(
        "src.main_app.public.main_routes.translate_routes.FilesService.download_and_save",
        fake_download,
    )


@pytest.fixture
def mock_inject(monkeypatch: pytest.MonkeyPatch):
    """Mock the inject step to write a dummy output file."""
    from src.main_app.shared.copysvg_wrapper.mapping import InjectResult

    def fake_inject(file_path, translations, output_file, overwrite_translations=False):
        # Write a dummy output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("<svg><text>Hello</text><text systemLanguage=\"ar\">مرحبا</text></svg>")
        return InjectResult(
            result=True,
            msg="1 languages injected",
            new_languages_count=1,
            inserted_translations=1,
            updated_translations=0,
        )

    monkeypatch.setattr(
        "src.main_app.public.main_routes.translate_routes.inject_step_one_file",
        fake_inject,
    )


class TestSelectForm:
    """GET /translate/ — select form."""

    def test_select_form_renders(self, mock_client):
        response = mock_client.get("/translate/")
        assert response.status_code == 200
        assert b"Interactive SVG Translate" in response.data


class TestSelectPost:
    """POST /translate/ — Commons file selection."""

    def test_empty_filename_shows_error(self, mock_client):
        response = mock_client.post(
            "/translate/",
            data={"filename": "", "lang": "ar"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Please provide a file name" in response.data

    def test_empty_lang_shows_error(self, mock_client):
        response = mock_client.post(
            "/translate/",
            data={"filename": "Test.svg", "lang": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Please select a target language" in response.data

    def test_invalid_filename_shows_error(self, mock_client):
        response = mock_client.post(
            "/translate/",
            data={"filename": "../etc/passwd", "lang": "ar"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid file name" in response.data

    def test_file_not_found_shows_error(self, mock_client, mocker: MockerFixture):
        mock_info = MagicMock()
        mock_info.exists = False
        mocker.patch(
            "src.main_app.public.main_routes.translate_routes.FilesService.get_file_info",
            return_value=mock_info,
        )
        response = mock_client.post(
            "/translate/",
            data={"filename": "Nonexistent.svg", "lang": "ar"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"does not exist on Commons" in response.data

    def test_strips_file_prefix(
        self,
        mock_client,
        mock_download,
        mock_extract,
    ):
        response = mock_client.post(
            "/translate/",
            data={"filename": "File:Test.svg", "lang": "ar"},
        )
        assert response.status_code == 302
        assert "/translate/" in response.headers["Location"]

    def test_successful_session_creation_redirects_to_edit(
        self,
        mock_client,
        mock_download,
        mock_extract,
    ):
        response = mock_client.post(
            "/translate/",
            data={"filename": "Test.svg", "lang": "ar"},
        )
        assert response.status_code == 302
        location = response.headers["Location"]
        assert "/translate/" in location
        assert "lang=ar" in location


class TestUploadPost:
    """POST /translate/upload — direct SVG upload."""

    def test_no_file_shows_error(self, mock_client):
        response = mock_client.post(
            "/translate/upload",
            data={"lang": "ar"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Please select an SVG file" in response.data

    def test_non_svg_rejected(self, mock_client):
        from io import BytesIO

        data = {"lang": "ar", "svg_file": (BytesIO(b"not svg"), "test.png")}
        response = mock_client.post(
            "/translate/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Only SVG files" in response.data

    def test_successful_upload_creates_session(
        self,
        mock_client,
        mock_extract,
    ):
        from io import BytesIO

        svg_content = b'<svg><text>Hello</text></svg>'
        data = {
            "lang": "ar",
            "svg_file": (BytesIO(svg_content), "test.svg"),
        }
        response = mock_client.post(
            "/translate/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 302
        assert "/translate/" in response.headers["Location"]
        assert "lang=ar" in response.headers["Location"]


class TestEditForm:
    """GET /translate/<session_id> — edit form."""

    def test_invalid_session_redirects(self, mock_client):
        response = mock_client.get("/translate/nonexistent-id", follow_redirects=True)
        assert response.status_code == 200
        assert b"Session expired" in response.data

    def test_edit_form_renders_rows(
        self,
        mock_client,
        mock_download,
        mock_extract,
    ):
        # Create session via POST
        response = mock_client.post(
            "/translate/",
            data={"filename": "Test.svg", "lang": "ar"},
        )
        session_id = response.headers["Location"].split("/translate/")[1].split("?")[0]

        # GET edit form
        response = mock_client.get(f"/translate/{session_id}?lang=ar")
        assert response.status_code == 200
        assert b"Hello" in response.data
        assert b"translateForm" in response.data


class TestCommitPost:
    """POST /translate/<session_id> — commit translations."""

    def _create_session(self, mock_client):
        """Helper to create a session and return its ID."""
        response = mock_client.post(
            "/translate/",
            data={"filename": "Test.svg", "lang": "ar"},
        )
        return response.headers["Location"].split("/translate/")[1].split("?")[0]

    def test_commit_no_data_warns(
        self,
        mock_client,
        mock_download,
        mock_extract,
    ):
        session_id = self._create_session(mock_client)

        response = mock_client.post(
            f"/translate/{session_id}",
            data={"lang": "ar"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"No translations were provided" in response.data

    def test_commit_with_translations(
        self,
        mock_client,
        mock_download,
        mock_extract,
        mock_inject,
    ):
        session_id = self._create_session(mock_client)

        response = mock_client.post(
            f"/translate/{session_id}",
            data={
                "lang": "ar",
                "source_0": "Hello",
                "target_0": "مرحبا",
                "source_1": "Goodbye",
                "target_1": "مع السلامة",
            },
        )
        assert response.status_code == 200
        assert b"Translations applied" in response.data
        assert b"Download SVG" in response.data

    def test_commit_expired_session_redirects(self, mock_client):
        response = mock_client.post(
            "/translate/nonexistent-id",
            data={"lang": "ar", "source_0": "Hello", "target_0": "Hi"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Session expired" in response.data


class TestDownloadGet:
    """GET /translate/<session_id>/download — download result SVG."""

    def test_download_no_output_redirects(self, mock_client, mock_download, mock_extract):
        # Create session
        response = mock_client.post(
            "/translate/",
            data={"filename": "Test.svg", "lang": "ar"},
        )
        session_id = response.headers["Location"].split("/translate/")[1].split("?")[0]

        # Try download without committing
        response = mock_client.get(
            f"/translate/{session_id}/download",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"No output file available" in response.data

    def test_download_after_commit(
        self,
        mock_client,
        mock_download,
        mock_extract,
        mock_inject,
    ):
        # Create session
        response = mock_client.post(
            "/translate/",
            data={"filename": "Test.svg", "lang": "ar"},
        )
        session_id = response.headers["Location"].split("/translate/")[1].split("?")[0]

        # Commit
        mock_client.post(
            f"/translate/{session_id}",
            data={
                "lang": "ar",
                "source_0": "Hello",
                "target_0": "مرحبا",
            },
        )

        # Download
        response = mock_client.get(f"/translate/{session_id}/download")
        assert response.status_code == 200
        assert "image/svg+xml" in response.content_type
        assert b"svg" in response.data
