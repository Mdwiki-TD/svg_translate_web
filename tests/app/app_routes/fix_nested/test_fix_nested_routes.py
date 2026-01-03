"""Tests for the fix_nested routes blueprint."""

from __future__ import annotations

import types
from typing import Any

import pytest
from flask import Flask

from src.app import create_app
from src.app.app_routes.fix_nested import routes


class DummyDatabase:
    """Minimal database stub."""

    def close(self) -> None:
        pass


class DummyFixNestedTaskStore:
    """In-memory task store for fix_nested tests."""

    def __init__(self, db: Any) -> None:
        self.tasks: dict[str, dict[str, Any]] = {}

    def create_task(self, task_id: str, filename: str, username: str | None = None) -> None:
        self.tasks[task_id] = {
            "id": task_id,
            "filename": filename,
            "username": username,
            "status": "pending",
        }

    def update_status(self, task_id: str, status: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status

    def update_error(self, task_id: str, error: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["error"] = error

    def update_download_result(self, task_id: str, result: dict[str, Any]) -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["download_result"] = result

    def update_nested_counts(
        self,
        task_id: str,
        *,
        before: int | None = None,
        after: int | None = None,
        fixed: int | None = None,
    ) -> None:
        if task_id in self.tasks:
            if before is not None:
                self.tasks[task_id]["nested_before"] = before
            if after is not None:
                self.tasks[task_id]["nested_after"] = after
            if fixed is not None:
                self.tasks[task_id]["nested_fixed"] = fixed

    def update_upload_result(self, task_id: str, result: dict[str, Any]) -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["upload_result"] = result


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch):
    """Provide a Flask test client for fix_nested routes."""
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

    monkeypatch.setattr(routes, "render_template", fake_render)
    return captured


def test_get_commons_file_url_basic() -> None:
    """Test Commons URL generation for a simple filename."""
    url = routes._get_commons_file_url("Example.svg")
    assert url == "https://commons.wikimedia.org/wiki/File:Example.svg"


def test_get_commons_file_url_with_spaces() -> None:
    """Test Commons URL generation replaces spaces with underscores."""
    url = routes._get_commons_file_url("Example File Name.svg")
    assert url == "https://commons.wikimedia.org/wiki/File:Example_File_Name.svg"


def test_get_commons_file_url_with_special_chars() -> None:
    """Test Commons URL generation encodes special characters."""
    url = routes._get_commons_file_url("Test (2024).svg")
    # Parentheses should be percent-encoded
    assert "File:Test_%282024%29.svg" in url


def test_fix_nested_get_empty_by_default(app_client: tuple[Flask, Any]) -> None:
    """Test that the form input is empty by default on GET."""
    app, client = app_client

    response = client.get("/fix_nested/")
    assert response.status_code == 200
    # The form input should have value="" (empty) by default
    assert b'value=""' in response.data


def test_fix_nested_get_restores_filename_from_session(
    app_client: tuple[Flask, Any],
) -> None:
    """Test that filename is restored from session after OAuth redirect."""
    app, client = app_client

    with client.session_transaction() as sess:
        sess[routes.FIX_NESTED_FILENAME_KEY] = "restored_file.svg"

    response = client.get("/fix_nested/")
    assert response.status_code == 200
    # The form should have the filename pre-filled
    assert b'value="restored_file.svg"' in response.data


def test_fix_nested_post_empty_filename_shows_error(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that submitting an empty filename shows an error."""
    app, _ = app_client

    user = types.SimpleNamespace(
        username="tester", access_token="tok", access_secret="sec", user_id=123
    )
    monkeypatch.setattr(routes, "current_user", lambda: user)

    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    monkeypatch.setattr(routes, "flash", fake_flash)

    with app.test_request_context("/fix_nested/", method="POST", data={"filename": ""}):
        result = routes.fix_nested_post()

    assert result == "rendered:fix_nested/form.html"
    assert ("Please provide a file name", "danger") in flashed


def test_fix_nested_post_preserves_filename_after_submission(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that filename persists in form after POST (regardless of result)."""
    app, _ = app_client

    user = types.SimpleNamespace(
        username="tester", access_token="tok", access_secret="sec", user_id=123
    )
    monkeypatch.setattr(routes, "current_user", lambda: user)

    # Mock process_fix_nested to return failure
    def mock_process(*args, **kwargs):
        return {"success": False, "message": "Download failed", "details": {}}

    monkeypatch.setattr(routes, "process_fix_nested", mock_process)
    monkeypatch.setattr(routes, "Database", lambda data: DummyDatabase())
    monkeypatch.setattr(routes, "FixNestedTaskStore", DummyFixNestedTaskStore)
    monkeypatch.setattr(routes, "flash", lambda *args: None)
    monkeypatch.setattr(routes, "load_auth_payload", lambda user: {})

    with app.test_request_context(
        "/fix_nested/", method="POST", data={"filename": "File:MyFile.svg"}
    ):
        routes.fix_nested_post()

    # The filename should remain in the form input
    assert patch_render["context"]["filename"] == "File:MyFile.svg"


def test_fix_nested_post_shows_commons_link_on_success(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that Commons link is displayed after successful upload."""
    app, _ = app_client

    user = types.SimpleNamespace(
        username="tester", access_token="tok", access_secret="sec", user_id=123
    )
    monkeypatch.setattr(routes, "current_user", lambda: user)

    # Mock process_fix_nested to return success
    def mock_process(*args, **kwargs):
        return {
            "success": True,
            "message": "Fixed 2 nested tags",
            "details": {"task_id": "test-id"},
        }

    monkeypatch.setattr(routes, "process_fix_nested", mock_process)
    monkeypatch.setattr(routes, "Database", lambda data: DummyDatabase())
    monkeypatch.setattr(routes, "FixNestedTaskStore", DummyFixNestedTaskStore)
    monkeypatch.setattr(routes, "flash", lambda *args: None)
    monkeypatch.setattr(routes, "load_auth_payload", lambda user: {})

    with app.test_request_context(
        "/fix_nested/", method="POST", data={"filename": "Success_Test.svg"}
    ):
        routes.fix_nested_post()

    # Check for Commons link in context
    commons_link = patch_render["context"].get("commons_link")
    assert commons_link == "https://commons.wikimedia.org/wiki/File:Success_Test.svg"


def test_fix_nested_post_strips_file_prefix(
    app_client: tuple[Flask, Any],
    monkeypatch: pytest.MonkeyPatch,
    patch_render: dict,
) -> None:
    """Test that 'File:' prefix is stripped correctly for processing."""
    app, _ = app_client

    user = types.SimpleNamespace(
        username="tester", access_token="tok", access_secret="sec", user_id=123
    )
    monkeypatch.setattr(routes, "current_user", lambda: user)

    captured_filename: list[str] = []

    def mock_process(filename, *args, **kwargs):
        captured_filename.append(filename)
        return {"success": False, "message": "Test", "details": {}}

    monkeypatch.setattr(routes, "process_fix_nested", mock_process)
    monkeypatch.setattr(routes, "Database", lambda data: DummyDatabase())
    monkeypatch.setattr(routes, "FixNestedTaskStore", DummyFixNestedTaskStore)
    monkeypatch.setattr(routes, "flash", lambda *args: None)
    monkeypatch.setattr(routes, "load_auth_payload", lambda user: {})

    with app.test_request_context(
        "/fix_nested/", method="POST", data={"filename": "File:WithPrefix.svg"}
    ):
        routes.fix_nested_post()

    assert captured_filename == ["WithPrefix.svg"]


def test_fix_nested_session_cleared_after_get(
    app_client: tuple[Flask, Any],
) -> None:
    """Test that session filename is cleared after being restored on GET."""
    app, client = app_client

    with client.session_transaction() as sess:
        sess[routes.FIX_NESTED_FILENAME_KEY] = "once_only.svg"

    # First GET should show the filename
    response1 = client.get("/fix_nested/")
    assert b'value="once_only.svg"' in response1.data

    # Second GET should show empty (session was cleared)
    response2 = client.get("/fix_nested/")
    assert b'value=""' in response2.data
