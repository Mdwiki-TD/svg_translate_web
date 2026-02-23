"""Tests for the tasks routes blueprint."""

from __future__ import annotations

import threading
import types
import uuid
from typing import Any

import pytest
from flask import Flask

from src.main_app import create_app
from src.main_app.app_routes.tasks import routes


class DummyTaskStore:
    """Lightweight in-memory task store used by the tests."""

    def __init__(self) -> None:
        self.tasks: dict[str, dict[str, Any]] = {}
        self.closed = False

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

    def list_tasks(
        self,
        *,
        username: str | None = None,
        order_by: str | None = None,
        descending: bool | None = None,
    ) -> list[dict[str, Any]]:
        del order_by
        del descending
        tasks = list(self.tasks.values())
        if username:
            tasks = [task for task in tasks if task.get("username") == username]
        return [dict(task) for task in tasks]

    def delete_task(self, task_id: str) -> None:
        if task_id not in self.tasks:
            raise LookupError("Task not found")
        del self.tasks[task_id]

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch):
    """Provide a Flask test client wired with an in-memory task store."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    store = DummyTaskStore()

    def store_factory() -> DummyTaskStore:
        return store

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes._task_store", store_factory)
    routes.TASK_STORE = store
    routes.TASKS_LOCK = threading.Lock()

    yield app, app.test_client(), store

    routes.TASK_STORE = None


def test_format_task_message() -> None:
    formatted = routes.format_task_message(
        [
            {
                "stages": {
                    "prepare": {"message": "download,convert"},
                    "upload": {"message": "single"},
                }
            },
            {"stages": {}},
        ]
    )

    assert formatted[0]["stages"]["prepare"]["message"] == "download<br>convert"
    assert formatted[0]["stages"]["upload"]["message"] == "single"


def test_close_task_store(monkeypatch: pytest.MonkeyPatch) -> None:
    store = DummyTaskStore()
    routes.TASK_STORE = store
    routes.close_task_store()
    assert store.closed is True

    routes.TASK_STORE = None
    # Should be a no-op when the store is already cleared.
    routes.close_task_store()


def test_task_redirects_without_identifier(app_client: tuple[Flask, Any, DummyTaskStore]) -> None:
    app, client, _ = app_client

    response = client.get("/task")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_task_renders_context_with_missing_task(
    app_client: tuple[Flask, Any, DummyTaskStore], monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, store = app_client
    store.tasks.clear()

    captured: dict[str, Any] = {}
    flashed: list[tuple[str, str]] = []

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.current_user", lambda: None)

    def fake_render(template: str, **context: Any) -> str:
        captured["template"] = template
        captured["context"] = context
        return "rendered"

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.render_template", fake_render)
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.flash", fake_flash)

    with app.test_request_context("/task/missing?title=Sample&error=task-active"):
        result = routes.task("missing")

    assert result == "rendered"
    assert captured["template"] == "task.html"
    assert captured["context"]["task"]["error"] == "not-found"
    assert captured["context"]["title"] == "Sample"
    assert flashed == [("A task for this title is already in progress.", "warning")]


def test_task2_includes_ordered_stages(
    app_client: tuple[Flask, Any, DummyTaskStore], monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _, store = app_client
    store.tasks["task42"] = {
        "id": "task42",
        "title": "Example",
        "stages": {
            "convert": {"number": 2, "message": "convert"},
            "download": {"number": 1, "message": "download"},
        },
        "form": {"field": "value"},
    }

    monkeypatch.setattr(
        "src.main_app.app_routes.tasks.routes.current_user", lambda: types.SimpleNamespace(username="demo")
    )

    captured: dict[str, Any] = {}

    def fake_render(template: str, **context: Any) -> str:
        captured["template"] = template
        captured["context"] = context
        return "rendered"

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.render_template", fake_render)

    with app.test_request_context("/task2/task42"):
        result = routes.task2("task42")

    assert result == "rendered"
    assert captured["template"] == "task2.html"
    assert [name for name, _ in captured["context"]["stages"]] == ["download", "convert"]
    assert captured["context"]["task"]["id"] == "task42"


def test_start_creates_task_and_launches_thread(
    app_client: tuple[Flask, Any, DummyTaskStore], monkeypatch: pytest.MonkeyPatch
) -> None:
    app, client, store = app_client

    user = types.SimpleNamespace(
        username="tester",
        access_token="token",
        access_secret="secret",
        user_id=1,
    )

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.current_user", lambda: user)
    monkeypatch.setattr("src.main_app.users.current.current_user", lambda: user)

    generated_id = "abc123"
    monkeypatch.setattr(uuid, "uuid4", lambda: types.SimpleNamespace(hex=generated_id))

    launch_calls: list[tuple[Any, ...]] = []

    def fake_launch(task_id: str, title: str, args: Any, auth_payload: dict[str, Any]) -> None:
        launch_calls.append((task_id, title, args, auth_payload))

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.launch_task_thread", fake_launch)

    response = client.post("/", data={"title": "Sample Title", "upload": "on"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/task/{generated_id}?title=Sample+Title")
    assert generated_id in store.tasks
    assert store.tasks[generated_id]["title"] == "Sample Title"
    assert launch_calls and launch_calls[0][0] == generated_id
    assert launch_calls[0][1] == "Sample Title"
    assert launch_calls[0][3]["username"] == "tester"


def test_start_redirects_to_existing_task_when_duplicate(
    app_client: tuple[Flask, Any, DummyTaskStore], monkeypatch: pytest.MonkeyPatch
) -> None:
    app, client, store = app_client

    user = types.SimpleNamespace(
        username="tester",
        access_token="token",
        access_secret="secret",
        user_id=1,
    )

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.current_user", lambda: user)
    monkeypatch.setattr("src.main_app.users.current.current_user", lambda: user)

    existing_id = "existing"
    store.create_task(existing_id, "Duplicate Title", username="tester", form={"title": "Duplicate Title"})

    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.flash", fake_flash)

    launch_calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        "src.main_app.app_routes.tasks.routes.launch_task_thread", lambda *args, **kwargs: launch_calls.append(args)
    )

    response = client.post("/", data={"title": "Duplicate Title"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/task/{existing_id}?title=Duplicate+Title")
    assert flashed == [("Task for title 'Duplicate Title' already exists: existing.", "warning")]
    assert not launch_calls


def test_status_returns_task_payload(app_client: tuple[Flask, Any, DummyTaskStore]) -> None:
    app, client, store = app_client

    store.tasks["task1"] = {"id": "task1", "status": "Pending"}

    missing = client.get("/status/missing")
    assert missing.status_code == 404
    assert missing.get_json() == {"error": "not-found"}

    response = client.get("/status/task1")
    assert response.status_code == 200
    assert response.get_json() == {"id": "task1", "status": "Pending"}


def test_tasks_renders_formatted_tasks(
    app_client: tuple[Flask, Any, DummyTaskStore], monkeypatch: pytest.MonkeyPatch
) -> None:
    app, client, store = app_client

    store.tasks["t1"] = {"id": "t1", "status": "Queued", "username": "alice"}
    store.tasks["t2"] = {"id": "t2", "status": "Completed", "username": "alice"}

    user = types.SimpleNamespace(username="alice")
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.current_user", lambda: user)

    formatted_inputs: list[list[dict[str, Any]]] = []

    def fake_format_task(task: dict[str, Any]) -> dict[str, Any]:
        return {"id": task["id"], "status": task.get("status")}

    def fake_format_message(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        formatted_inputs.append(values)
        return [{"id": item["id"], "status": item["status"], "processed": True} for item in values]

    captured: dict[str, Any] = {}

    def fake_render(template: str, **context: Any) -> str:
        captured["template"] = template
        captured["context"] = context
        return "rendered"

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.format_task", fake_format_task)
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.format_task_message", fake_format_message)
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.render_template", fake_render)

    response = client.get("/tasks/alice")

    assert response.status_code == 200
    assert response.data == b"rendered"
    assert captured["template"] == "tasks.html"
    assert captured["context"]["tasks"] == [
        {"id": "t1", "status": "Queued", "processed": True},
        {"id": "t2", "status": "Completed", "processed": True},
    ]
    assert captured["context"]["available_statuses"] == ["Completed", "Queued"]
    assert captured["context"]["is_own_tasks"] is True
    assert formatted_inputs and len(formatted_inputs[0]) == 2


def test_delete_task_success(app_client: tuple[Flask, Any, DummyTaskStore], monkeypatch: pytest.MonkeyPatch) -> None:
    app, client, store = app_client

    store.tasks["deadbeef"] = {"id": "deadbeef", "title": "Delete me"}

    user = types.SimpleNamespace(username="admin")
    monkeypatch.setattr("src.main_app.admins.admins_required.current_user", lambda: user)
    monkeypatch.setattr("src.main_app.admins.admins_required.active_coordinators", lambda: ["admin"])

    flashed: list[tuple[str, str]] = []

    def fake_flash(message: str, category: str) -> None:
        flashed.append((message, category))

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.flash", fake_flash)

    response = client.post("/task/deadbeef/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/tasks")
    assert "deadbeef" not in store.tasks
    assert flashed == [("Task 'deadbeef' removed.", "success")]
