"""Unit tests for task routes URL fix."""

from __future__ import annotations

import threading
import types
from typing import Any

import pytest
from flask import Flask

from src.main_app import create_app
from src.main_app.app_routes.copy_svg_langs_job import routes


class DummyTaskStore:
    """Lightweight in-memory task store used by the tests."""

    def __init__(self) -> None:
        self.tasks: dict[str, dict[str, Any]] = {}

    def create_task(
        self,
        task_id: str,
        title: str,
        *,
        username: str = "",
        form: dict[str, Any] | None = None,
    ) -> None:
        if task_id in self.tasks:
            raise ValueError(f"Task {task_id} already exists")
        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "username": username,
            "status": "Pending",
            "form": dict(form or {}),
        }

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        task = self.tasks.get(task_id)
        return dict(task) if task else None

    def get_active_task_by_title(self, title: str) -> dict[str, Any] | None:
        for task in self.tasks.values():
            if task["title"] == title and task.get("status") not in {"Completed", "Failed", "Cancelled"}:
                return dict(task)
        return None

    def close(self) -> None:
        pass


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch):
    """Provide a Flask test client wired with an in-memory task store."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    store = DummyTaskStore()

    monkeypatch.setattr("src.main_app.app_routes.copy_svg_langs_job.routes._task_store", lambda: store)
    monkeypatch.setattr("src.main_app.services.copy_svg_langs_service.TASK_STORE", store)
    monkeypatch.setattr("src.main_app.services.copy_svg_langs_service.TASK_STORE_LOCK", threading.Lock())

    yield app, app.test_client(), store


def test_start_redirects_to_correct_task_endpoint(
    app_client: tuple[Flask, Any, DummyTaskStore], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that start() redirects to the existing task when a duplicate is found."""
    app, client, store = app_client

    user = types.SimpleNamespace(
        username="tester",
        access_token="token",
        access_secret="secret",
        user_id=1,
    )

    monkeypatch.setattr("src.main_app.app_routes.copy_svg_langs_job.routes.current_user", lambda: user)
    monkeypatch.setattr("src.main_app.services.users_service.current_user", lambda: user)

    existing_id = "existing-task-123"
    store.create_task(existing_id, "Test Title", username="tester", form={"title": "Test Title"})

    response = client.post("/start", data={"title": "Test Title"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/tasks/{existing_id}?title=Test+Title")
