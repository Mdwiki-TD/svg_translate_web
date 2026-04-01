"""Tests for cancel and restart routes."""

from __future__ import annotations

import types

import pytest
from flask import Flask

from src.main_app.public_jobs_workers.copy_svg_langs_legacy import routes
from src.main_app.config import DbConfig


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    """
    Create a Flask test application configured with patched settings and helpers for cancel/restart route tests.

    The fixture constructs a Flask app with a secret key, injects a DbConfig-based settings object into the cancel/restart routes module, and monkeypatches route helpers (`flash`, `jsonify`, `redirect`, `url_for`) and `current_user` to provide predictable behavior for tests. Yields the configured Flask application for use in request contexts.

    Returns:
        Flask: A Flask application instance with the above test-specific patches applied.
    """
    app = Flask(__name__)
    app.secret_key = "secret"

    settings = types.SimpleNamespace(
        database_data=DbConfig(
            db_name="",
            db_host="",
            db_user=None,
            db_password=None,
        ),
        disable_uploads="",
    )
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.settings", settings)

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.flash", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.jsonify", lambda payload: payload)
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.redirect", lambda url: {"redirect_to": url})
    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.url_for",
        lambda endpoint, **kwargs: f"url_for({endpoint}, {kwargs})",
    )

    # Mock current_user in the module where oauth_required is defined
    import src.main_app.services.users_service

    monkeypatch.setattr(
        src.main_app.services.users_service, "current_user", lambda: types.SimpleNamespace(username="user")
    )

    yield app


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

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes._task_store", lambda: DummyStore())
    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.current_user", lambda: types.SimpleNamespace(username="user")
    )
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.active_coordinators", lambda: ["user"])
    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.get_cancel_event", lambda task_id, store=None: DummyEvent()
    )

    with app.test_request_context("/tasks/1/cancel"):
        response = routes.cancel("task")

    assert response == {"redirect_to": "url_for(tasks.task_infos, {'task_id': 'task'})"}
    assert cancel_called == ["set"]


def test_restart_creates_new_task(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    created_tasks: list[tuple[str, dict[str, str]]] = []
    launched: list[tuple[str, str]] = []

    def fake_get_store_task(task_id: str) -> dict[str, object]:
        return {
            "id": task_id,
            "title": "Sample",
            "username": "user",
            "form": {"param": "value"},
        }

    def fake_create_new_task(task_id: str, title: str, *, username: str, form: dict | None = None) -> None:
        created_tasks.append((task_id, {"title": title, "username": username, "form": form}))

    def fake_parse_args(form, disable_uploads):
        return types.SimpleNamespace(parsed="ok")

    def fake_launch(task_id: str, title: str, args, user_payload: dict) -> None:
        launched.append((task_id, user_payload["username"]))

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.get_store_task", fake_get_store_task)
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.create_new_task", fake_create_new_task)
    monkeypatch.setattr(
        routes,
        "current_user",
        lambda: types.SimpleNamespace(user_id=1, username="user", access_token="tok", access_secret="sec"),
    )
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.parse_args", fake_parse_args)
    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.uuid",
        types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="newtask")),
    )
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.start_copy_svg_langs_job", fake_launch)

    with app.test_request_context("/tasks/1/restart"):
        response = routes.restart("task")

    assert response == {"redirect_to": "url_for(tasks.task_infos, {'task_id': 'newtask'})"}
    assert created_tasks[0][0] == "newtask"
    assert launched == [("newtask", "user")]


def test_cancel_task_not_found(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> None:
            return None

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes._task_store", lambda: DummyStore())

    with app.test_request_context("/tasks/missing/cancel"):
        response = routes.cancel("missing")

    assert response == {"redirect_to": "url_for(main.index, {})"}


def test_cancel_task_already_completed(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> dict[str, str]:
            return {"id": task_id, "status": "Completed"}

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes._task_store", lambda: DummyStore())

    with app.test_request_context("/tasks/1/cancel"):
        response = routes.cancel("1")

    assert response == {"redirect_to": "url_for(tasks.task_infos, {'task_id': '1'})"}


def test_cancel_task_wrong_owner(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> dict[str, str]:
            return {"id": task_id, "status": "Running", "username": "other_user"}

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes._task_store", lambda: DummyStore())
    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.current_user", lambda: types.SimpleNamespace(username="user")
    )
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.active_coordinators", list)

    with app.test_request_context("/tasks/1/cancel"):
        response = routes.cancel("1")

    assert response == {"redirect_to": "url_for(tasks.task_infos, {'task_id': '1'})"}


def test_restart_task_not_found(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStore:
        def get_task(self, task_id: str) -> None:
            return None

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes._task_store", lambda: DummyStore())

    with app.test_request_context("/tasks/missing/restart"):
        response = routes.restart("missing")

    assert response == {"redirect_to": "url_for(main.index, {})"}


def test_restart_task_collision(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.main_app.db import TaskAlreadyExistsError

    def fake_get_store_task(task_id: str) -> dict[str, object]:
        return {"id": task_id, "title": "Sample", "username": "user", "form": {}}

    def fake_create_new_task(*args, **kwargs) -> None:
        raise TaskAlreadyExistsError({"id": "existing_id"})

    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.get_store_task", fake_get_store_task)
    monkeypatch.setattr("src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.create_new_task", fake_create_new_task)
    monkeypatch.setattr(
        routes,
        "current_user",
        lambda: types.SimpleNamespace(user_id=1, username="user", access_token="tok", access_secret="sec"),
    )
    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.routes.parse_args", lambda f, d: types.SimpleNamespace()
    )

    with app.test_request_context("/tasks/1/restart"):
        response = routes.restart("1")

    assert response == {"redirect_to": "url_for(tasks.task_infos, {'task_id': 'existing_id'})"}
