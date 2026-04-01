from unittest.mock import MagicMock

import pytest
import logging
from unittest.mock import Mock

from src.main_app.app_routes.copy_svg_langs_job.copy_svg_langs_db.db_CreateUpdate import CreateUpdateTask, TaskAlreadyExistsError
from src.main_app.db.utils import DbUtils


class MockCreateUpdateTask(CreateUpdateTask, DbUtils):
    def fetch_stages(self, task_id):
        return {}


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def store(mock_db):
    return MockCreateUpdateTask(db=mock_db)


def test_TaskAlreadyExistsError():
    task = {"id": 1, "title": "dup"}
    err = TaskAlreadyExistsError(task)
    assert str(err) == "Task with this title is already in progress"
    assert err.task == task


def test_delete_task_success(store, mock_db):
    store.delete_task("t1")
    mock_db.execute_query.assert_called_with(
        "\n                DELETE FROM tasks\n                WHERE id = %s\n                ", ["t1"]
    )


def test_delete_task_exception(store, mock_db):
    mock_db.execute_query.side_effect = Exception("error")
    with pytest.raises(Exception, match="error"):
        store.delete_task("t1")


def test_create_task_success(store, mock_db):
    mock_db.fetch_query.return_value = []  # No existing task

    store.create_task("t1", "Title 1")

    mock_db.execute_query.assert_called()
    args = mock_db.execute_query.call_args[0]
    assert "INSERT INTO tasks" in args[0]
    assert args[1][0] == "t1"  # id
    assert args[1][2] == "Title 1"  # title
    assert args[1][3] == "title 1"  # normalized_title


def test_create_task_already_exists(store, mock_db):
    # Mock return for check query
    mock_db.fetch_query.return_value = [
        {
            "id": "existing",
            "title": "Title 1",
            "normalized_title": "title 1",
            "status": "Pending",
            "created_at": "2023-01-01",
            "updated_at": "2023-01-01",
            "form_json": None,
            "data_json": None,
            "results_json": None,
            "main_file": None,
        }
    ]

    with pytest.raises(TaskAlreadyExistsError) as exc:
        store.create_task("t2", "Title 1")  # Same title

    assert exc.value.task["id"] == "existing"


def test_create_task_ignore_existing(store, mock_db):
    mock_db.fetch_query.return_value = [{"id": "existing", "title": "Title 1"}]

    # Should not raise
    store.create_task("t2", "Title 1", form={"ignore_existing_task": True})

    mock_db.execute_query.assert_called()


def test_get_task_success(store, mock_db):
    mock_db.fetch_query_safe.return_value = [
        {
            "id": "t1",
            "title": "T",
            "status": "Pending",
            "created_at": "2023-01-01",
            "updated_at": "2023-01-01",
            "normalized_title": "t",
            "form_json": None,
            "data_json": None,
            "results_json": None,
            "main_file": None,
        }
    ]

    task = store.get_task("t1")
    assert task["id"] == "t1"
    assert task["title"] == "T"


def test_get_task_not_found(store, mock_db):
    mock_db.fetch_query_safe.return_value = []
    assert store.get_task("unknown") is None


def test_get_active_task_by_title_success(store, mock_db):
    mock_db.fetch_query_safe.return_value = [
        {
            "id": "t1",
            "title": " My Title ",
            "status": "Pending",
            "created_at": "2023-01-01",
            "updated_at": "2023-01-01",
            "normalized_title": "my title",
            "form_json": None,
            "data_json": None,
            "results_json": None,
            "main_file": None,
        }
    ]

    task = store.get_active_task_by_title("My Title")
    assert task["id"] == "t1"

    # Check normalized title use
    args = mock_db.fetch_query_safe.call_args[0]
    assert args[1][0] == "my title"


def test_update_task_fields(store, mock_db):
    store.update_task("t1", title="New Title", status="Done", form={"a": 1})

    mock_db.execute_query.assert_called()
    args = mock_db.execute_query.call_args[0]
    sql = args[0]
    params = args[1]

    assert "UPDATE tasks" in sql
    assert params[0] == "New Title"  # title
    assert params[1] == "new title"  # normalized
    assert params[3] == "Done"  # status
    assert params[4] == '{"a": 1}'  # form_json
    assert params[8] == "t1"  # id


def test_update_task_no_change(store, mock_db):
    store.update_task("t1")
    mock_db.execute_query.assert_not_called()


def test_update_helpers(store, mock_db):
    # Just verify they call update_task -> execute_query

    store.update_status("t1", "Done")
    mock_db.execute_query.assert_called()

    mock_db.reset_mock()
    store.update_data("t1", {"d": 1})
    mock_db.execute_query.assert_called()

    mock_db.reset_mock()
    store.update_results("t1", {"r": 1})
    mock_db.execute_query.assert_called()

    mock_db.reset_mock()
    store.update_main_title("t1", "file.svg")
    mock_db.execute_query.assert_called()


def test_update_task_one_column(store, mock_db):
    store.update_task_one_column("t1", "status", "Done")
    mock_db.execute_query.assert_called()
    assert "SET status = %s" in mock_db.execute_query.call_args[0][0]


def test_update_task_one_column_illegal(store, mock_db):
    store.update_task_one_column("t1", "bad_col", "val")
    mock_db.execute_query.assert_not_called()


def test_delete_task_success1(caplog):
    """Test successful task deletion with info logging."""
    mock_db = Mock()
    mock_db.execute_query = Mock(return_value=1)

    task_store = CreateUpdateTask(db=mock_db)

    with caplog.at_level(logging.INFO):
        task_store.delete_task("task123")

    mock_db.execute_query.assert_called_once()
    assert "Task task123 deleted successfully" in caplog.text


def test_delete_task_raises_and_logs_exception(caplog):
    """Test that delete_task logs exception and re-raises."""
    mock_db = Mock()
    mock_db.execute_query = Mock(side_effect=Exception("Database error"))

    task_store = CreateUpdateTask(db=mock_db)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Database error"):
            task_store.delete_task("task456")

    # Verify that logger.exception was called (logs at ERROR level with traceback)
    assert "Failed to delete task" in caplog.text
    assert "Database error" in caplog.text


def test_delete_task_sql_injection_prevention():
    """Test that delete_task uses parameterized queries."""
    mock_db = Mock()

    task_store = CreateUpdateTask(db=mock_db)
    task_store.delete_task("task' OR '1'='1")

    # Verify parameterized query
    call_args = mock_db.execute_query.call_args
    assert call_args[0][0].strip().startswith("DELETE FROM tasks")
    assert call_args[0][1] == ["task' OR '1'='1"]


def test_task_already_exists_error_stores_task():
    """Test TaskAlreadyExistsError stores the conflicting task."""
    conflicting_task = {"id": "task123", "title": "Test"}

    error = TaskAlreadyExistsError(conflicting_task)

    assert error.task == conflicting_task
    assert "Task with this title is already in progress" in str(error)
