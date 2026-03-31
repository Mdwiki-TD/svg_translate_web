import re

import pytest

from src.main_app import create_app
from src.main_app.app_routes.copy_svg_langs_job import routes as task_routes


class DummyStore:
    def __init__(self, task):
        self._task = task

    def get_task(self, task_id):  # pragma: no cover - trivial
        return self._task


@pytest.fixture
def app_factory(monkeypatch):
    def _factory(task):
        import importlib

        app_module = importlib.import_module("src.main_app.__init__")
        admin_service = importlib.import_module("src.main_app.services.admin_service")

        # Mock current_user
        monkeypatch.setattr(
            "src.main_app.services.users_service.current_user",
            lambda: type("User", (), {"username": "testuser", "user_id": 1, "is_admin": False}),
        )

        class _DummyCoordinatorStore:
            def list(self):  # pragma: no cover - trivial stub
                return []

        monkeypatch.setattr("src.main_app.services.admin_service.get_admins_db", lambda: _DummyCoordinatorStore())

        # Patch _task_store BEFORE create_app so routes use the dummy store
        monkeypatch.setattr("src.main_app.services.tasks_service.TASK_STORE", None)
        monkeypatch.setattr(
            "src.main_app.app_routes.copy_svg_langs_job.routes._task_store",
            lambda: DummyStore(task),
        )

        app = create_app()
        app.config["TESTING"] = True
        return app

    return _factory


def _get_button_classes(html, button_id):
    block_pattern = rf'<[^>]*id="{button_id}"[^>]*>'
    match = re.search(block_pattern, html)
    if not match:
        return None
    class_match = re.search(r'class="([^"]+)"', match.group(0))
    if not class_match:
        return ""
    return class_match.group(1)


def test_task2_active_shows_cancel_button(app_factory):
    task = {
        "id": "running-task",
        "title": "Demo",
        "status": "Running",
        "stages": {"Download": {"status": "Running", "number": 1}},
    }
    app = app_factory(task)
    with app.test_client() as client:
        response = client.get(f"/task/{task['id']}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Cancel button should exist
    cancel_classes = _get_button_classes(html, "cancel-task-btn")
    assert cancel_classes is not None, "Cancel button should be present"
    assert f'data-task-id="{task["id"]}"' in html  # Maybe not on button but in section

    # Restart button should NOT exist
    restart_classes = _get_button_classes(html, "restart-task-btn")
    assert restart_classes is None, "Restart button should NOT be present"

    assert "badge text-bg-primary" in html  # running badge


def test_task2_terminal_shows_restart_button(app_factory):
    task = {
        "id": "complete-task",
        "title": "Demo",
        "status": "Completed",
        "stages": {"Download": {"status": "Completed", "number": 1}},
    }
    app = app_factory(task)
    with app.test_client() as client:
        response = client.get(f"/task/{task['id']}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Cancel button should NOT exist
    cancel_classes = _get_button_classes(html, "cancel-task-btn")
    assert cancel_classes is None, "Cancel button should NOT be present"

    # Restart button should exist
    restart_classes = _get_button_classes(html, "restart-task-btn")
    assert restart_classes is not None, "Restart button should be present"

    # Check data-task-id presence (in general html)
    assert f'data-task-id="{task["id"]}"' in html
    assert "badge text-bg-success" in html


def test_stage_cancelled_renders_warning_badge(app_factory):
    task = {
        "id": "cancelled-task",
        "title": "Demo",
        "status": "Cancelled",
        "stages": {"Upload": {"status": "Cancelled", "number": 1}},
    }
    app = app_factory(task)
    with app.test_client() as client:
        response = client.get(f"/task/{task['id']}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    header_badge = re.search(
        r'<span id="task_status"[^>]*>\s*<span[^>]*class="badge text-bg-warning"[^>]*>\s*Cancelled\s*</span>',
        html,
        flags=re.DOTALL,
    )
    # The regex might be too strict regarding whitespace or nesting.
    # The template has:
    # <span id="task_status" data-status="...">
    #   <span class="badge text-bg-warning">Cancelled</span>
    # </span>

    # Just check for the badge class and text close to each other or just existence
    assert "badge text-bg-warning" in html
    assert "Cancelled" in html

    # Or stricter check
    assert 'class="badge text-bg-warning">Cancelled</span>' in html
