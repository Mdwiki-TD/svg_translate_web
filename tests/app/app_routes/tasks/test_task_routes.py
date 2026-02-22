import threading
from typing import Any, Dict, Optional

import pytest

from src.app import create_app
from src.app.app_routes.tasks import routes
from src.app.db import TaskAlreadyExistsError
from src.app.threads import task_threads, web_run_task


class InMemoryTaskStore:
    def __init__(self) -> None:
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_task(
        self,
        task_id: str,
        title: str,
        status: str = "Pending",
        username: str = "",
        form: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            if task_id in self.tasks:
                raise TaskAlreadyExistsError(self.tasks[task_id])
            self.tasks[task_id] = {
                "id": task_id,
                "title": title,
                "username": username,
                "status": status,
                "form": dict(form or {}),
            }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self.tasks.get(task_id)
            return dict(task) if task else None

    def get_active_task_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for task in self.tasks.values():
                if task["title"] == title and task["status"] not in {"Completed", "Failed", "Cancelled"}:
                    return dict(task)
        return None

    def update_status(self, task_id: str, status: str) -> None:
        with self._lock:
            if task_id in self.tasks:
                updated = dict(self.tasks[task_id])
                updated["status"] = status
                self.tasks[task_id] = updated

    def update_stage(
        self, task_id: str, stage_name: str, stage_state: Dict[str, Any]
    ) -> None:  # pragma: no cover - unused
        pass

    def update_results(self, task_id: str, results: Dict[str, Any]) -> None:  # pragma: no cover - unused
        pass

    def update_data(self, task_id: str, data: Dict[str, Any]) -> None:  # pragma: no cover - unused
        pass

    def close(self) -> None:  # pragma: no cover - interface compatibility
        pass


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    """
    Create and configure a Flask application for tests with an in-memory task store and mocked authentication.

    This fixture sets FLASK_SECRET_KEY, enables testing mode, disables WTForms CSRF, installs an InMemoryTaskStore and a threading lock into route modules, clears global task cancellation events, and patches `current_user` to a test user for authentication checks.

    Parameters:
        monkeypatch (pytest.MonkeyPatch): Fixture used to set environment variables and patch module attributes for the test.

    Returns:
        app: A Flask application instance configured for testing.
    """
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    store = InMemoryTaskStore()

    # Patch task store in tasks routes
    monkeypatch.setattr(routes, "_task_store", lambda: store)
    # Patch task store in cancel_restart routes
    monkeypatch.setattr("src.app.app_routes.cancel_restart.routes._task_store", lambda: store)

    routes.TASK_STORE = store
    routes.TASKS_LOCK = threading.Lock()
    with task_threads.CANCEL_EVENTS_LOCK:
        task_threads.CANCEL_EVENTS.clear()

    # Mock current user for auth checks
    monkeypatch.setattr("src.app.users.current.current_user", lambda: type('User', (), {'username': 'testuser', 'user_id': 1, 'access_token': 'tok', 'access_secret': 'sec'}))
    monkeypatch.setattr("src.app.app_routes.cancel_restart.routes.current_user", lambda: type('User', (), {'username': 'testuser', 'user_id': 1, 'access_token': 'tok', 'access_secret': 'sec'}))

    return app


def test_cancel_route_signals_event_and_updates_status(app: Any, monkeypatch: pytest.MonkeyPatch):
    # Retrieve store from routes since we patched it
    store: InMemoryTaskStore = routes._task_store()  # type: ignore[assignment]

    # Create a task first
    task_id = "test-task-1"
    store.create_task(task_id, "Sample", username="testuser")

    # Register cancel event
    cancel_event = threading.Event()
    with task_threads.CANCEL_EVENTS_LOCK:
        task_threads.CANCEL_EVENTS[task_id] = cancel_event

    client = app.test_client()

    cancel_response = client.post(f"/tasks/{task_id}/cancel")
    assert cancel_response.status_code == 302  # Redirects back to task page

    assert store.tasks[task_id]["status"] == "Cancelled"
    assert cancel_event.is_set()


def test_restart_route_creates_new_task_and_replays_form(app: Any, monkeypatch: pytest.MonkeyPatch):
    store: InMemoryTaskStore = routes._task_store()  # type: ignore[assignment]

    existing_id = "existing"
    store.create_task(existing_id, "Title", form={"title": "Title", "titles_limit": "5", "upload": "on"}, username="testuser")
    store.update_status(existing_id, "Cancelled")

    captured: Dict[str, Any] = {}

    task_finished = threading.Event()

    def fake_run_task(db_data, task_id, title, args, user_payload, *, cancel_event=None):
        """
        Record the provided task invocation inputs into the test capture and signal completion.

        This test helper stores the received values into the surrounding `captured` mapping and sets the `task_finished` event to indicate the fake task has run.

        Parameters:
            db_data: Database context or placeholder passed by the caller (not used by the helper).
            task_id: Identifier of the task being "run".
            title: Task title.
            args: Arguments object passed to the task runner.
            user_payload: Payload supplied by the user when launching the task.
            cancel_event (threading.Event | None): Optional event that would be used to signal cancellation; recorded for inspection.
        """
        captured["task_id"] = task_id
        captured["title"] = title
        captured["args"] = args
        captured["user_payload"] = user_payload
        captured["cancel_event"] = cancel_event
        task_finished.set()

    monkeypatch.setattr("src.app.app_routes.cancel_restart.routes.launch_task_thread",
                        lambda tid, t, a, p: fake_run_task(None, tid, t, a, p, cancel_event=threading.Event()))

    # Mock uuid to return a predictable ID for the new task is hard if uuid is used inside routes.
    # But we can capture the ID from the run_task call or the response location.

    client = app.test_client()
    restart_response = client.post(f"/tasks/{existing_id}/restart")
    assert restart_response.status_code == 302

    # Wait for the thread/fake runner
    assert task_finished.wait(timeout=1), "The fake_run_task did not run in time."

    new_task_id = captured["task_id"]
    assert new_task_id != existing_id
    assert new_task_id in store.tasks
    assert store.tasks[new_task_id]["title"] == "Title"
    assert store.tasks[new_task_id]["form"] == {"title": "Title", "titles_limit": "5", "upload": "on"}

    assert captured["title"] == "Title"
    assert hasattr(captured["args"], "titles_limit")
    assert captured["args"].titles_limit == 5


def test_no_mysql_connection_attempted_with_default_settings(monkeypatch: pytest.MonkeyPatch):
    """
    Test that ensures no MySQL connection is attempted when create_app() is
    called with default test settings. This is achieved by patching the Database
    class and asserting that it is not instantiated.
    """
    database_init = threading.Event()

    def fake_database(*args, **kwargs):
        database_init.set()
        raise Exception("MySQL connection should not be attempted")

    monkeypatch.setattr("src.app.db.db_class.Database", fake_database)

    app = create_app()

    # Assert that the fake_database was not initialized, meaning no MySQL connection was attempted.
    assert not database_init.is_set()
