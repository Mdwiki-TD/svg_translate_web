"""Unit tests for task routes URL fix."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

from flask import Flask

from src.main_app.app_routes.tasks import routes


def test_start_redirects_to_correct_task_endpoint(monkeypatch):
    """Test that start() redirects to 'tasks.task'."""
    app = Flask(__name__)
    app.secret_key = "test"

    mock_task_store = Mock()
    mock_task_store.get_active_task_by_title = Mock(return_value={"id": "existing-task-123", "status": "Pending"})

    monkeypatch.setattr("src.main_app.app_routes.tasks.routes._task_store", lambda: mock_task_store)
    monkeypatch.setattr(
        "src.main_app.app_routes.tasks.routes.get_active_task_by_title", mock_task_store.get_active_task_by_title
    )

    mock_args = Mock()
    mock_args.ignore_existing_task = False
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.parse_args", Mock(return_value=mock_args))
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.create_new_task", Mock())
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.launch_task_thread", Mock())

    with app.test_request_context(method="POST", data={"title": "Test Title"}):
        with patch("src.main_app.users.current.current_user") as mock_user:
            mock_user.return_value = Mock(username="testuser", user_id=1, access_token="tok", access_secret="sec")

            with patch("src.main_app.app_routes.tasks.routes.flash"):
                with patch("src.main_app.app_routes.tasks.routes.redirect"):
                    with patch("src.main_app.app_routes.tasks.routes.url_for") as mock_url_for:
                        mock_url_for.return_value = "/task/existing-task-123"

                        routes.start()

                        mock_url_for.assert_any_call(
                            "tasks.task",
                            task_id="existing-task-123",
                            title="Test Title",
                        )
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.parse_args", Mock())
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.create_new_task", Mock())
    monkeypatch.setattr("src.main_app.app_routes.tasks.routes.launch_task_thread", Mock())

    with app.test_request_context(method="POST", data={"title": "Test Title"}):
        with patch("src.main_app.users.current.current_user") as mock_user:
            mock_user.return_value = Mock(username="testuser", user_id=1, access_token="tok", access_secret="sec")

            with patch("src.main_app.app_routes.tasks.routes.flash"):
                with patch("src.main_app.app_routes.tasks.routes.redirect"):
                    with patch("src.main_app.app_routes.tasks.routes.url_for") as mock_url_for:
                        mock_url_for.return_value = "/task/existing-task-123"

                        routes.start()

                        mock_url_for.assert_any_call(
                            "tasks.task",
                            task_id="existing-task-123",
                            title="Test Title",
                        )
