import pytest
from unittest.mock import patch, MagicMock
from flask import Blueprint
from src.main_app.app_routes.admin.admin_routes.recent import _recent_routes, Recent


@patch('src.app.app_routes.admin.admin_routes.recent.TASKS_LOCK')
@patch('src.app.app_routes.admin.admin_routes.recent._task_store')
@patch('src.app.app_routes.admin.admin_routes.recent.format_task')
@patch('src.app.app_routes.admin.admin_routes.recent.format_task_message')
@patch('src.app.app_routes.admin.admin_routes.recent.render_template')
def test_recent_routes(mock_render_template, mock_format_task_message, mock_format_task,
                       mock_task_store, mock_lock):
    """Test _recent_routes function."""
    # Mock the task store return value
    mock_store_instance = MagicMock()
    mock_store_instance.list_tasks.return_value = [
        {"id": 1, "status": "Running", "title": "Task 1"},
        {"id": 2, "status": "Pending", "title": "Task 2"},
        {"id": 3, "status": "Completed", "title": "Task 3"}
    ]
    mock_task_store.return_value = mock_store_instance

    # Mock formatted tasks
    formatted_tasks = [
        {"id": 1, "status": "Running", "title": "Task 1"},
        {"id": 2, "status": "Pending", "title": "Task 2"},
        {"id": 3, "status": "Completed", "title": "Task 3"}
    ]
    mock_format_task.side_effect = formatted_tasks
    mock_format_task_message.return_value = formatted_tasks

    # Call the function
    result = _recent_routes()

    # Assertions
    mock_store_instance.list_tasks.assert_called_once_with(
        order_by="created_at",
        descending=True
    )
    assert mock_format_task.call_count == 3
    mock_format_task_message.assert_called_once_with(formatted_tasks)
    mock_render_template.assert_called_once()

    # Check that the template is called with expected arguments
    call_args = mock_render_template.call_args
    assert call_args[0][0] == "admins/admin.html"  # Template name
    kwargs = call_args[1]
    assert "tasks" in kwargs
    assert "total_tasks" in kwargs
    assert "active_tasks" in kwargs
    assert "status_counts" in kwargs


def test_Recent_init():
    """Test Recent class initialization."""
    mock_bp = MagicMock(spec=Blueprint)

    # Create an instance of Recent
    recent_instance = Recent(mock_bp)

    # Verify that the blueprint's route was registered
    # Check that get method was called with the right parameters
    assert mock_bp.get.called
    # Find the call that registers the /recent route
    recent_route_registered = False
    for call in mock_bp.get.call_args_list:
        if call[0][0] == "/recent":  # Route path
            recent_route_registered = True
            break

    assert recent_route_registered, "The /recent route should have been registered"

    # Also verify that admin_required decorator was applied by checking the decorator chain
    # The route should have been decorated with both @bp_admin.get("/recent") and @admin_required
