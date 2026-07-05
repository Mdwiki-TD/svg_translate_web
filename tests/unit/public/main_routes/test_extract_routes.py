"""Unit tests for src/main_app/public/main_routes/extract_routes.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.public.main_routes import extract_routes


@pytest.fixture
def patch_render(monkeypatch: pytest.MonkeyPatch) -> dict:
    captured: dict[str, dict] = {}

    def fake_render(template: str, **context):
        captured["template"] = template
        captured["context"] = context
        return f"rendered:{template}"

    monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.render_template", fake_render)
    return captured


class TestExtractGet:
    def test_returns_form(self, monkeypatch, patch_render):
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.session", {"pop": lambda k, d="": d})
        result = extract_routes.extract_translations()
        assert "form" in result

    def test_restores_filename_from_session(self, monkeypatch, patch_render):
        session = {}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.session", session)
        session[extract_routes.EXTRACT_FILENAME_KEY] = "test.svg"
        result = extract_routes.extract_translations()
        assert "form" in result


class TestExtractPost:
    def test_empty_filename(self, monkeypatch, patch_render):
        flashed = []
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", lambda m, c: flashed.append((m, c)))
        mock_req = MagicMock()
        mock_req.form.get.return_value = ""
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.request", mock_req)
        result = extract_routes.extract_translations_post()
        assert "form" in result
        assert any("Please provide a file name" in m for m, c in flashed)

    def test_strips_file_prefix(self, monkeypatch, tmp_path):
        mock_download = MagicMock()
        mock_download.return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.download_one_file", mock_download)
        mock_extract = MagicMock()
        mock_extract.return_value = {"new": {}, "title": {}}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.extract", mock_extract)
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.tempfile.mkdtemp", lambda: str(tmp_path))
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.shutil.rmtree", MagicMock())
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", MagicMock())
        monkeypatch.setattr(
            "src.main_app.public.main_routes.extract_routes.render_template", lambda t, **c: f"rendered:{t}"
        )

        mock_req = MagicMock()
        mock_req.form.get.return_value = "File: Test.svg"
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.request", mock_req)
        extract_routes.extract_translations_post()
        mock_download.assert_called_once_with(title="Test.svg", out_dir=tmp_path, i=0, overwrite=True)

    def test_download_failure(self, monkeypatch, patch_render, tmp_path):
        flashed = []
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", lambda m, c: flashed.append((m, c)))
        mock_download = MagicMock()
        mock_download.return_value = {"result": "failed", "path": ""}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.download_one_file", mock_download)
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.tempfile.mkdtemp", lambda: str(tmp_path))
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.shutil.rmtree", MagicMock())
        mock_req = MagicMock()
        mock_req.form.get.return_value = "Test.svg"
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.request", mock_req)
        result = extract_routes.extract_translations_post()
        assert "form" in result
        assert any("Failed to download file" in m for m, c in flashed)

    def test_extraction_error(self, monkeypatch, patch_render, tmp_path):
        flashed = []
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", lambda m, c: flashed.append((m, c)))
        mock_download = MagicMock()
        mock_download.return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.download_one_file", mock_download)
        mock_extract = MagicMock()
        mock_extract.side_effect = ValueError("Invalid SVG")
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.extract", mock_extract)
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.tempfile.mkdtemp", lambda: str(tmp_path))
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.shutil.rmtree", MagicMock())
        mock_req = MagicMock()
        mock_req.form.get.return_value = "Test.svg"
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.request", mock_req)
        result = extract_routes.extract_translations_post()
        assert "form" in result
        assert any("An error occurred while extracting translations" in m for m, c in flashed)

    def test_invalid_translations_type(self, monkeypatch, patch_render, tmp_path):
        flashed = []
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", lambda m, c: flashed.append((m, c)))
        mock_download = MagicMock()
        mock_download.return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.download_one_file", mock_download)
        mock_extract = MagicMock()
        mock_extract.return_value = "not_a_dict"
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.extract", mock_extract)
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.tempfile.mkdtemp", lambda: str(tmp_path))
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.shutil.rmtree", MagicMock())
        mock_req = MagicMock()
        mock_req.form.get.return_value = "Test.svg"
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.request", mock_req)
        result = extract_routes.extract_translations_post()
        assert "form" in result
        assert any("Invalid or empty translation data" in m for m, c in flashed)

    def test_successful_extraction(self, monkeypatch, patch_render, tmp_path):
        flashed = []
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", lambda m, c: flashed.append((m, c)))
        mock_download = MagicMock()
        mock_download.return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.download_one_file", mock_download)
        sample = {"new": {"hello": {"ar": "مرحبا"}}, "title": {}}
        monkeypatch.setattr(
            "src.main_app.public.main_routes.extract_routes.extract", lambda svg_file_path, case_insensitive: sample
        )
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.tempfile.mkdtemp", lambda: str(tmp_path))
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.shutil.rmtree", MagicMock())
        mock_req = MagicMock()
        mock_req.form.get.return_value = "Test.svg"
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.request", mock_req)
        result = extract_routes.extract_translations_post()
        assert "result" in result
        assert ("Translations extracted successfully", "success") in flashed

    def test_languages_extracted(self, monkeypatch, patch_render, tmp_path):
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.flash", MagicMock())
        mock_download = MagicMock()
        mock_download.return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.download_one_file", mock_download)
        sample = {"new": {"key1": {"ar": "a", "fr": "b"}, "key2": {"ar": "c", "de": "d"}}, "title": {}}
        monkeypatch.setattr(
            "src.main_app.public.main_routes.extract_routes.extract", lambda svg_file_path, case_insensitive: sample
        )
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.tempfile.mkdtemp", lambda: str(tmp_path))
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.shutil.rmtree", MagicMock())
        mock_req = MagicMock()
        mock_req.form.get.return_value = "Test.svg"
        monkeypatch.setattr("src.main_app.public.main_routes.extract_routes.request", mock_req)
        extract_routes.extract_translations_post()
        assert patch_render["context"]["languages"] == ["ar", "de", "fr"]
