"""Unit tests for task routes URL fix."""
from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
from flask import Flask

from src.app.app_routes.tasks import routes


def test_start_redirects_to_correct_task_endpoint(monkeypatch):
    """Test that start() redirects to 'tasks.task' not 'tasks.task1'."""
    app = Flask(__name__)
    app.secret_key = "test"
    
    # Mock the necessary dependencies
    mock_task_store = Mock()
    mock_task_store.get_active_task_by_title = Mock(return_value={"id": "existing-task-123", "status": "Pending"})

    monkeypatch.setattr("src.app.app_routes.tasks.routes._task_store", lambda: mock_task_store)
    # Patch TASKS_LOCK to avoid threading issues in tests
    monkeypatch.setattr("src.app.app_routes.tasks.routes.TASKS_LOCK", MagicMock())

    with app.test_request_context(method="POST", data={"title": "Test Title"}):
        # Patch current_user where it's defined to satisfy oauth_required
        with patch("src.app.users.current.current_user") as mock_user:
            mock_user.return_value = Mock(username="testuser", user_id=1, access_token="tok", access_secret="sec")
            
            with patch("src.app.app_routes.tasks.routes.flash"):
                with patch("src.app.app_routes.tasks.routes.redirect"):
                    with patch("src.app.app_routes.tasks.routes.url_for") as mock_url_for:
                        with patch("src.app.app_routes.tasks.routes.launch_task_thread"):
                            mock_url_for.return_value = "/task/existing-task-123"

                            routes.start()

                            # Verify url_for was called with correct endpoint name
                            mock_url_for.assert_any_call(
                                "tasks.task",  # Should be 'task' not 'task1'
                                task_id="existing-task-123",
                                title="Test Title",
                            )


def test_logger_uses_svg_translate_name():
    """Test that the logger uses 'svg_translate' instead of __name__."""
    assert routes.logger.name == "svg_translate"
