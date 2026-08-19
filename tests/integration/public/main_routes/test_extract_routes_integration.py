"""Tests for the extract translations endpoint."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.public.main_routes.extract_routes import EXTRACT_FILENAME_KEY
from src.main_app.services.copysvg_wrapper.extract_translations import TranslationMapping


@pytest.fixture(autouse=True)
def setup_tests(mocker, monkeypatch, tmp_path):
    def mock_mkdtemp():
        return str(tmp_path / "test_dir")

    monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.tempfile.mkdtemp", mock_mkdtemp)

    _mock = MagicMock()
    _mock.exists = True
    mocker.patch("src.main_app.public.main_routes.extract_routes.FilesService.get_file_info", return_value=_mock)

    monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.shutil.rmtree", lambda *args: None)


@pytest.fixture
def mock_flash(monkeypatch):
    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", fake_flash)
    yield flashed


def test_extract_get_empty_by_default(mock_client) -> None:
    """Test that the extract form input is empty by default on GET."""
    response = mock_client.get("/extract/")
    assert response.status_code == 200
    assert b'value=""' in response.data


def test_extract_get_restores_filename_from_session(mock_client) -> None:
    """Test that filename is restored from session after OAuth redirect."""

    with mock_client.session_transaction() as sess:
        sess[EXTRACT_FILENAME_KEY] = "test_file.svg"

    response = mock_client.get("/extract/")
    assert response.status_code == 200
    assert b'value="test_file.svg"' in response.data


@pytest.fixture
def patch_render(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Mock render_template to capture context without template processing."""
    captured: dict[str, Any] = {}

    def fake_render(template: str, **context):
        captured["template"] = template
        captured["context"] = context
        return f"rendered:{template}"

    monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.render_template", fake_render)
    return captured


class TestExtractPost:

    def test_extract_post_empty_filename_shows_error(
        self,
        mock_client,
        patch_render: dict,
        mock_flash,
    ) -> None:
        """Test that submitting an empty filename shows an error."""

        response = mock_client.post(
            "/extract/",
            data={"filename": ""},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert response.data.decode() == "rendered:extract/form.html"
        assert ("Please provide a file name", "danger") in mock_flash

    def test_extract_post_download_failure(
        self,
        mock_client,
        monkeypatch: pytest.MonkeyPatch,
        patch_render: dict,
        mock_flash,
        tmp_path,
    ) -> None:
        """Test that download failure shows appropriate error."""

        def mock_download(*args, **kwargs):
            return DownloadAndSaveData(result="failed", path="")

        monkeypatch.setattr(
            "src.main_app.public.main_routes.extract_routes.FilesService.download_and_save", mock_download
        )

        response = mock_client.post(
            "/extract/",
            data={"filename": "Test.svg"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert response.data.decode() == "rendered:extract/result.html"
        assert any("Failed to download file" in msg for msg, cat in mock_flash)


class TestExtractRender:

    def test_extract_post_strips_file_prefix(
        self,
        mock_client,
        patch_render: dict,
        mocker: MockerFixture,
        tmp_path,
        mock_flash,
    ) -> None:
        """Test that 'File:' prefix is stripped from filename."""

        mock_download = mocker.patch("src.main_app.public.main_routes.extract_routes.FilesService.download_and_save")
        mock_download.return_value = DownloadAndSaveData(result="success", path=str(tmp_path / "test_dir/test.svg"))

        mock_extract = mocker.patch(
            "src.main_app.services.copysvg_wrapper.extract_translations._extract_file_translations"
        )
        mock_extract.return_value = TranslationMapping(new={})

        mock_client.post(
            "/extract/",
            data={"filename": "File: Test.svg"},
            follow_redirects=True,
        )

        mock_download.assert_called_once_with(title="Test.svg", out_dir=mocker.ANY, overwrite_download=True)

        assert patch_render["context"]["filename"] == "File:Test.svg"

    def test_extract_post_extraction_error(
        self,
        mock_client,
        monkeypatch: pytest.MonkeyPatch,
        patch_render: dict,
        mock_flash,
        tmp_path,
    ) -> None:
        """Test that extraction error shows appropriate error."""

        def mock_download(*args, **kwargs):
            return DownloadAndSaveData(result="success", path=str(tmp_path / "test.svg"))

        def mock_extract(*args, **kwargs):
            raise ValueError("Invalid SVG format")

        monkeypatch.setattr(
            "src.main_app.public.main_routes.extract_routes.FilesService.download_and_save", mock_download
        )
        monkeypatch.setattr(
            "src.main_app.services.copysvg_wrapper.extract_translations._extract_file_translations",
            mock_extract,
        )

        response = mock_client.post(
            "/extract/",
            data={"filename": "Test.svg"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert response.data.decode() == "rendered:extract/result.html"

    def test_extract_post_successful_extraction(
        self,
        mock_client,
        monkeypatch: pytest.MonkeyPatch,
        patch_render: dict,
        tmp_path,
        mock_flash,
    ) -> None:
        """Test successful extraction returns proper context."""

        def mock_download(*args, **kwargs):
            return DownloadAndSaveData(result="success", path=str(tmp_path / "test.svg"))

        sample_translations = {
            "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}},
            "title_new": {"music in {year}": {"ar": "الموسيقى في عام {year}", "fr": "La musique en {year}"}},
        }

        def mock_extract(*args, **kwargs):
            return TranslationMapping.from_any(sample_translations)

        monkeypatch.setattr(
            "src.main_app.public.main_routes.extract_routes.FilesService.download_and_save", mock_download
        )
        monkeypatch.setattr(
            "src.main_app.services.copysvg_wrapper.extract_translations._extract_file_translations",
            mock_extract,
        )

        response = mock_client.post(
            "/extract/",
            data={"filename": "Test.svg"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert response.data.decode() == "rendered:extract/result.html"
        assert ("Translations extracted successfully", "success") in mock_flash
        assert patch_render["context"]["translations"]["new"] == sample_translations["new"]
