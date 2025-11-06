"""
Tests for task routes.
"""
from unittest.mock import MagicMock, patch

from flask import Blueprint, Flask
import pytest

from src.app.app_routes.tasks.routes import bp_tasks, format_task_message


@pytest.fixture
def app():
    """Create a Flask app instance for testing."""
    app = Flask(__name__, template_folder='../../../../src/templates')
    app.secret_key = 'test-secret'
    app.register_blueprint(bp_tasks, url_prefix='/tasks')

    # Create dummy blueprints and filters for url_for calls in templates
    main_bp = Blueprint('main', __name__)
    @main_bp.route('/')
    def index():
        return 'main.index'
    app.register_blueprint(main_bp)

    templates_bp = Blueprint('templates', __name__)
    @templates_bp.route('/templates')
    def main():
        return 'templates.main'
    app.register_blueprint(templates_bp)

    explorer_bp = Blueprint('explorer', __name__)
    @explorer_bp.route('/explorer')
    def main():
        return 'explorer.main'
    app.register_blueprint(explorer_bp)

    auth_bp = Blueprint('auth', __name__)
    @auth_bp.route('/login')
    def login():
        return 'auth.login'
    @auth_bp.route('/logout')
    def logout():
        return 'auth.logout'
    app.register_blueprint(auth_bp)

    @app.template_filter()
    def format_stage_timestamp(timestamp):
        return timestamp

    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


def test_format_task_message():
    """
    Tests the format_task_message function.
    """
    formatted = [
        {"stages": {"stage1": {"message": "msg1,msg2"}}}
    ]
    result = format_task_message(formatted)
    assert result[0]['stages']['stage1']['message'] == 'msg1<br>msg2'


@patch('src.app.app_routes.tasks.routes._task_store')
def test_task_found(mock_task_store, client):
    """
    Tests the task page when a task is found.
    """
    mock_store = MagicMock()
    mock_store.get_task.return_value = {"title": "Test Task"}
    mock_task_store.return_value = mock_store

    response = client.get('/tasks/task/123')
    assert response.status_code == 200
    assert b'Test Task' in response.data


@patch('src.app.app_routes.tasks.routes._task_store')
def test_task2_found(mock_task_store, client):
    """
    Tests the task2 page when a task is found.
    """
    mock_store = MagicMock()
    mock_store.get_task.return_value = {"title": "Test Task", "stages": {}}
    mock_task_store.return_value = mock_store

    response = client.get('/tasks/task2/123')
    assert response.status_code == 200
    assert b'Test Task' in response.data


@patch('src.app.app_routes.tasks.routes._task_store')
@patch('src.app.app_routes.tasks.routes.oauth_required', lambda fn: fn)
@patch('src.app.app_routes.tasks.routes.current_user', return_value=MagicMock(username='test'))
@patch('src.app.app_routes.tasks.routes.launch_task_thread')
def test_start_task(mock_launch, mock_user, mock_task_store, client):
    """
    Tests starting a new task.
    """
    mock_store = MagicMock()
    mock_store.get_active_task_by_title.return_value = None
    mock_task_store.return_value = mock_store

    response = client.post('/tasks/', data={'title': 'New Task'})
    assert response.status_code == 302
    assert '/tasks/task/' in response.headers['Location']
    mock_store.create_task.assert_called_once()
    mock_launch.assert_called_once()


@patch('src.app.app_routes.tasks.routes._task_store')
def test_status_found(mock_task_store, client):
    """
    Tests the status route when a task is found.
    """
    mock_store = MagicMock()
    mock_store.get_task.return_value = {"status": "Running"}
    mock_task_store.return_value = mock_store

    response = client.get('/tasks/status/123')
    assert response.status_code == 200
    assert response.json == {"status": "Running"}


@patch('src.app.app_routes.tasks.routes._task_store')
@patch('src.app.app_routes.tasks.routes.current_user', return_value=MagicMock(username='test'))
def test_tasks_list(mock_user, mock_task_store, client):
    """
    Tests the tasks list page.
    """
    mock_store = MagicMock()
    mock_store.list_tasks.return_value = [{"id": "123", "title": "Task 1"}]
    mock_task_store.return_value = mock_store

    response = client.get('/tasks/tasks/test')
    assert response.status_code == 200
    assert b'Task 1' in response.data
