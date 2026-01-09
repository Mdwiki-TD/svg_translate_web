"""Tests for cancel and restart routes."""

from __future__ import annotations

import types

import pytest
from flask import Flask

from src.app.app_routes.cancel_restart import routes


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) :
    app = Flask(__name__)
    app.secret_key = "secret"

    settings = types.SimpleNamespace(db_data={})
    monkeypatch.setattr(routes, "settings", settings)

    monkeypatch.setattr(routes, "flash", lambda *args, **kwargs: None)
    monkeypatch.setattr(routes, "jsonify", lambda payload: payload)
    monkeypatch.setattr(routes, "redirect", lambda url: {"redirect_to": url})
    monkeypatch.setattr(routes, "url_for", lambda endpoint, **kwargs: f"url_for({endpoint}, {kwargs})")

    # Mock current_user in the module where oauth_required is defined
    import src.app.users.current
    monkeypatch.setattr(src.app.users.current, "current_user", lambda: types.SimpleNamespace(username="user"))

    yield app


def test_login_required_json_blocks_anonymous(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routes, "current_user", lambda: None)

    @routes.login_required_json
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    with app.test_request_context("/"):
        response = protected()

    assert response == {"error": "login-required"}


def test_cancel_happy_path(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    cancel_called = []

    class DummyEvent:
        def set(self) -> None:
            cancel_called.append("set")

    class DummyStore:
        def __init__(self) -> None:
            self.updated: list[str] = []

        def get_task(self, task_id: str) -> dict[str, str]:
            return {"id": task_id, "status": "Running", "username": "user"}

        def update_status(self, task_id: str, status: str) -> None:
            self.updated.append((task_id, status))

    monkeypatch.setattr(routes, "_task_store", lambda: DummyStore())
    monkeypatch.setattr(routes, "current_user", lambda: types.SimpleNamespace(username="user"))
    monkeypatch.setattr(routes, "active_coordinators", lambda: ["user"])
    monkeypatch.setattr(routes, "get_cancel_event", lambda task_id: DummyEvent())

    with app.test_request_context("/tasks/1/cancel"):
        response = routes.cancel("task")

    assert response == {"redirect_to": "url_for(tasks.task, {'task_id': 'task'})"}
    assert cancel_called == ["set"]


def test_restart_creates_new_task(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    created_tasks: list[tuple[str, dict[str, str]]] = []
    launched: list[tuple[str, str]] = []

    class DummyStore:
        def get_task(self, task_id: str) -> dict[str, object]:
            return {
                "id": task_id,
                "title": "Sample",
                "username": "user",
                "form": {"param": "value"},
            }

        def create_task(self, task_id: str, title: str, *, username: str, form: dict | None = None) -> None:
            created_tasks.append((task_id, {"title": title, "username": username, "form": form}))

    def fake_parse_args(form):
        return types.SimpleNamespace(parsed="ok")

    def fake_launch(task_id: str, title: str, args, user_payload: dict) -> None:
        launched.append((task_id, user_payload["username"]))

    monkeypatch.setattr(routes, "_task_store", lambda: DummyStore())
    monkeypatch.setattr(routes, "current_user", lambda: types.SimpleNamespace(
        user_id=1, username="user", access_token="tok", access_secret="sec"
    ))
    monkeypatch.setattr(routes, "parse_args", fake_parse_args)
    monkeypatch.setattr(routes, "uuid", types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="newtask")))
    monkeypatch.setattr(routes, "launch_task_thread", fake_launch)

    with app.test_request_context("/tasks/1/restart"):
        response = routes.restart("task")

    assert response == {"redirect_to": "url_for(tasks.task, {'task_id': 'newtask'})"}
    assert created_tasks[0][0] == "newtask"
    assert launched == [("newtask", "user")]


def test_cancel_task_not_found(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> None:
            return None

    monkeypatch.setattr(routes, "_task_store", lambda: DummyStore())

    with app.test_request_context("/tasks/missing/cancel"):
        response = routes.cancel("missing")

    assert response == {"redirect_to": "url_for(main.index, {})"}


def test_cancel_task_already_completed(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> dict[str, str]:
            return {"id": task_id, "status": "Completed"}

    monkeypatch.setattr(routes, "_task_store", lambda: DummyStore())

    with app.test_request_context("/tasks/1/cancel"):
        response = routes.cancel("1")

    assert response == {"redirect_to": "url_for(tasks.task, {'task_id': '1'})"}


def test_cancel_task_wrong_owner(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> dict[str, str]:
            return {"id": task_id, "status": "Running", "username": "other_user"}

    monkeypatch.setattr(routes, "_task_store", lambda: DummyStore())
    monkeypatch.setattr(routes, "current_user", lambda: types.SimpleNamespace(username="user"))
    monkeypatch.setattr(routes, "active_coordinators", lambda: [])

    with app.test_request_context("/tasks/1/cancel"):
        response = routes.cancel("1")

    assert response == {"redirect_to": "url_for(tasks.task, {'task_id': '1'})"}


def test_restart_task_not_found(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> None:
            return None

    monkeypatch.setattr(routes, "_task_store", lambda: DummyStore())

    with app.test_request_context("/tasks/missing/restart"):
        response = routes.restart("missing")

    assert response == {"redirect_to": "url_for(main.index, {})"}


def test_restart_task_collision(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.app.db import TaskAlreadyExistsError

    class DummyStore:
        def get_task(self, task_id: str) -> dict[str, object]:
            return {"id": task_id, "title": "Sample", "username": "user", "form": {}}

        def create_task(self, *args, **kwargs) -> None:
            raise TaskAlreadyExistsError("exists", task={"id": "existing_id"})

    monkeypatch.setattr(routes, "_task_store", lambda: DummyStore())
    monkeypatch.setattr(routes, "current_user", lambda: types.SimpleNamespace(
        user_id=1, username="user", access_token="tok", access_secret="sec"
    ))
    monkeypatch.setattr(routes, "parse_args", lambda f: types.SimpleNamespace())

    with app.test_request_context("/tasks/1/restart"):
        response = routes.restart("1")

    assert response == {"redirect_to": "url_for(tasks.task, {'task_id': 'existing_id'})"}
