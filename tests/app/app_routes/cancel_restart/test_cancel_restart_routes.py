"""
Tests for task cancellation and restart routes.
"""
from unittest.mock import MagicMock, patch

from flask import Flask, g, jsonify
import pytest

from src.app.app_routes.cancel_restart.routes import bp_tasks_managers, login_required_json


@pytest.fixture
def app():
    """Create a Flask app instance for testing."""
    app = Flask(__name__)
    app.secret_key = 'test-secret'
    app.register_blueprint(bp_tasks_managers)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


def test_login_required_json_not_logged_in(app):
    """
    Tests that a user who is not logged in gets a JSON error.
    """
    @app.route('/protected')
    @login_required_json
    def protected_route():
        return jsonify(success=True)

    with app.test_request_context('/protected'), patch('src.app.app_routes.cancel_restart.routes.current_user', return_value=None):
        response = protected_route()
        assert response.json == {"error": "login-required"}


def test_login_required_json_logged_in(app):
    """
    Tests that a logged-in user can access the protected route.
    """
    @app.route('/protected')
    @login_required_json
    def protected_route():
        return jsonify(success=True)

    with app.test_request_context('/protected'), patch('src.app.app_routes.cancel_restart.routes.current_user', return_value=MagicMock()):
        response = protected_route()
        assert response.json == {"success": True}


@patch('src.app.app_routes.cancel_restart.routes._task_store')
@patch('src.app.app_routes.cancel_restart.routes.current_user')
def test_cancel_success(mock_current_user, mock_task_store, client):
    """
    Tests successful task cancellation.
    """
    mock_store = MagicMock()
    mock_store.get_task.return_value = {"status": "Running", "username": "testuser"}
    mock_task_store.return_value = mock_store
    mock_current_user.return_value = MagicMock(username="testuser")

    response = client.post('/tasks/123/cancel')
    assert response.status_code == 200
    assert response.json == {"task_id": "123", "status": "Cancelled"}
    mock_store.update_status.assert_called_once_with("123", "Cancelled")


@patch('src.app.app_routes.cancel_restart.routes._task_store')
@patch('src.app.app_routes.cancel_restart.routes.current_user')
@patch('src.app.app_routes.cancel_restart.routes.launch_task_thread')
def test_restart_success(mock_launch, mock_current_user, mock_task_store, client):
    """
    Tests successful task restart.
    """
    mock_store = MagicMock()
    mock_store.get_task.return_value = {"title": "Test Task", "form": {}}
    mock_task_store.return_value = mock_store
    mock_user = MagicMock(username="testuser", user_id=1)
    mock_current_user.return_value = mock_user

    response = client.post('/tasks/123/restart')
    assert response.status_code == 200
    assert response.json['status'] == "Running"
    mock_store.create_task.assert_called_once()
    mock_launch.assert_called_once()
