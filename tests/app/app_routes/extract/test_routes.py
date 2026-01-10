"""Tests for the extract translations endpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from flask import Flask

from src.app import create_app
from src.app.app_routes.extract import routes


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch):
    """Provide a Flask test client for extract routes."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    app = create_app()
    app.config["TESTING"] = True
    yield app, app.test_client()


@pytest.fixture
def patch_render(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Mock render_template to capture context without template processing."""
    captured: dict[str, Any] = {}

    def fake_render(template: str, **context):
        captured["template"] = template
        captured["context"] = context
        return f"rendered:{template}"

    monkeypatch.setattr("src.app.app_routes.extract.routes.render_template", fake_render)
    return captured


def test_extract_get_empty_by_default(app_client: tuple[Flask, Any]) -> None:
    """Test that the extract form input is empty by default on GET."""
    app, client = app_client

    response = client.get("/extract/")
    assert response.status_code == 200
    # The form input should have value="" (empty) by default
    assert b'value=""' in response.data


def test_extract_get_restores_filename_from_session(app_client: tuple[Flask, Any]) -> None:
    """Test that filename is restored from session after OAuth redirect."""
    app, client = app_client

    with client.session_transaction() as sess:
        sess[routes.EXTRACT_FILENAME_KEY] = "test_file.svg"

    response = client.get("/extract/")
    assert response.status_code == 200
    # The form should have the filename pre-filled
    assert b'value="test_file.svg"' in response.data


def test_extract_post_empty_filename_shows_error(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that submitting an empty filename shows an error."""
    app, _ = app_client

    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    monkeypatch.setattr("src.app.app_routes.extract.routes.flash", fake_flash)

    with app.test_request_context("/extract/", method="POST", data={"filename": ""}):
        result = routes.extract_translations_post()

    assert result == "rendered:extract/form.html"
    assert ("Please provide a file name", "danger") in flashed


def test_extract_post_strips_file_prefix(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that 'File:' prefix is stripped from filename."""
    app, _ = app_client

    # Mock download_one_file to simulate successful download
    def mock_download(*args, **kwargs):
        return {"result": "success", "path": "/tmp/test.svg"}

    # Mock extract to return sample data
    def mock_extract(*args, **kwargs):
        return {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}, "title": {}}

    # Mock Path and tempfile
    mock_temp_dir = MagicMock()
    mock_temp_dir.exists.return_value = True
    mock_temp_dir.__truediv__ = lambda self, other: Path(f"/tmp/{other}")

    def mock_mkdtemp():
        return "/tmp/test_dir"

    monkeypatch.setattr("src.app.app_routes.extract.routes.download_one_file", mock_download)
    monkeypatch.setattr("src.app.app_routes.extract.routes.extract", mock_extract)
    monkeypatch.setattr("src.app.app_routes.extract.routes.tempfile.mkdtemp", mock_mkdtemp)
    monkeypatch.setattr("src.app.app_routes.extract.routes.shutil.rmtree", lambda *args: None)
    monkeypatch.setattr("src.app.app_routes.extract.routes.flash", lambda *args: None)

    with app.test_request_context("/extract/", method="POST", data={"filename": "File:Test.svg"}):
        routes.extract_translations_post()

    # Verify the filename passed to download_one_file doesn't have "File:" prefix
    # We can check this indirectly through the patch_render context
    assert patch_render["context"]["filename"] == "File:Test.svg"


def test_extract_post_download_failure(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that download failure shows appropriate error."""
    app, _ = app_client

    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    # Mock download_one_file to simulate failure
    def mock_download(*args, **kwargs):
        return {"result": "failed", "path": ""}

    mock_temp_dir = MagicMock()
    mock_temp_dir.exists.return_value = True

    def mock_mkdtemp():
        return "/tmp/test_dir"

    monkeypatch.setattr("src.app.app_routes.extract.routes.download_one_file", mock_download)
    monkeypatch.setattr("src.app.app_routes.extract.routes.flash", fake_flash)
    monkeypatch.setattr("src.app.app_routes.extract.routes.tempfile.mkdtemp", mock_mkdtemp)
    monkeypatch.setattr("src.app.app_routes.extract.routes.shutil.rmtree", lambda *args: None)

    with app.test_request_context("/extract/", method="POST", data={"filename": "Test.svg"}):
        result = routes.extract_translations_post()

    assert result == "rendered:extract/form.html"
    assert any("Failed to download file" in msg for msg, cat in flashed)


def test_extract_post_extraction_error(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that extraction error shows appropriate error."""
    app, _ = app_client

    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    # Mock download_one_file to simulate success
    def mock_download(*args, **kwargs):
        return {"result": "success", "path": "/tmp/test.svg"}

    # Mock extract to raise an exception
    def mock_extract(*args, **kwargs):
        raise ValueError("Invalid SVG format")

    def mock_mkdtemp():
        return "/tmp/test_dir"

    monkeypatch.setattr("src.app.app_routes.extract.routes.download_one_file", mock_download)
    monkeypatch.setattr("src.app.app_routes.extract.routes.extract", mock_extract)
    monkeypatch.setattr("src.app.app_routes.extract.routes.flash", fake_flash)
    monkeypatch.setattr("src.app.app_routes.extract.routes.tempfile.mkdtemp", mock_mkdtemp)
    monkeypatch.setattr("src.app.app_routes.extract.routes.shutil.rmtree", lambda *args: None)

    with app.test_request_context("/extract/", method="POST", data={"filename": "Test.svg"}):
        result = routes.extract_translations_post()

    assert result == "rendered:extract/form.html"
    assert any("Error extracting translations" in msg for msg, cat in flashed)


def test_extract_post_successful_extraction(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test successful extraction returns proper context."""
    app, _ = app_client

    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    # Mock download_one_file to simulate success
    def mock_download(*args, **kwargs):
        return {"result": "success", "path": "/tmp/test.svg"}

    # Mock extract to return sample data
    sample_translations = {
        "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}},
        "title": {"music in": {"ar": "الموسيقى في عام", "fr": "La musique en"}},
    }

    def mock_extract(*args, **kwargs):
        return sample_translations

    def mock_mkdtemp():
        return "/tmp/test_dir"

    monkeypatch.setattr("src.app.app_routes.extract.routes.download_one_file", mock_download)
    monkeypatch.setattr("src.app.app_routes.extract.routes.extract", mock_extract)
    monkeypatch.setattr("src.app.app_routes.extract.routes.flash", fake_flash)
    monkeypatch.setattr("src.app.app_routes.extract.routes.tempfile.mkdtemp", mock_mkdtemp)
    monkeypatch.setattr("src.app.app_routes.extract.routes.shutil.rmtree", lambda *args: None)

    with app.test_request_context("/extract/", method="POST", data={"filename": "Test.svg"}):
        result = routes.extract_translations_post()

    assert result == "rendered:extract/result.html"
    assert ("Translations extracted successfully", "success") in flashed
    assert patch_render["context"]["translations"] == sample_translations
    assert "translations_json" in patch_render["context"]

    # Verify JSON is properly formatted
    json_data = json.loads(patch_render["context"]["translations_json"])
    assert json_data == sample_translations
