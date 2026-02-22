import pytest
import json
from unittest.mock import MagicMock
from src.main_app.db.fix_nested_task_store import FixNestedTaskStore

@pytest.fixture
def mock_db_class(mocker):
    return mocker.patch("src.app.db.fix_nested_task_store.Database")

@pytest.fixture
def mock_db_instance(mock_db_class):
    instance = MagicMock()
    return instance

@pytest.fixture
def store(mock_db_instance):
    return FixNestedTaskStore(db=mock_db_instance)

def test_init_schema(store, mock_db_instance):
    mock_db_instance.execute_query_safe.assert_called()
    assert "CREATE TABLE IF NOT EXISTS fix_nested_tasks" in mock_db_instance.execute_query_safe.call_args[0][0]

def test_create_task_success(store, mock_db_instance):
    res = store.create_task("t1", "file_name.svg", "user1")
    assert res is True

    args = mock_db_instance.execute_query_safe.call_args[0]
    assert "INSERT INTO fix_nested_tasks" in args[0]
    # Check filename normalized (replace _ with space)
    assert args[1][2] == "file name.svg"

def test_create_task_failure(store, mock_db_instance):
    mock_db_instance.execute_query_safe.side_effect = Exception("error")
    assert store.create_task("t1", "f", "u") is False

def test_get_task_success(store, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": "t1",
        "download_result": '{"a": 1}',
        "upload_result": None
    }]

    task = store.get_task("t1")
    assert task["id"] == "t1"
    assert task["download_result"] == {"a": 1}

def test_get_task_json_error(store, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": "t1",
        "download_result": '{invalid}',
        "upload_result": None
    }]

    task = store.get_task("t1")
    # Should leave raw string on error or handle gracefully?
    # Implementation swallows exception so it stays as string
    assert task["download_result"] == '{invalid}'

def test_get_task_not_found(store, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = []
    assert store.get_task("t1") is None

def test_update_status(store, mock_db_instance):
    assert store.update_status("t1", "running") is True
    mock_db_instance.execute_query_safe.assert_called()
    assert "UPDATE fix_nested_tasks SET status" in mock_db_instance.execute_query_safe.call_args[0][0]

def test_update_nested_counts(store, mock_db_instance):
    # Reset mock after init calls
    mock_db_instance.reset_mock()

    # Case 1: All None
    assert store.update_nested_counts("t1") is True
    mock_db_instance.execute_query_safe.assert_not_called()

    # Case 2: Update some
    store.update_nested_counts("t1", before=10, fixed=5)

def test_update_download_result(store, mock_db_instance):
    store.update_download_result("t1", {"res": "ok"})
    args = mock_db_instance.execute_query_safe.call_args[0]
    assert "download_result = %s" in args[0]
    assert args[1][0] == '{"res": "ok"}'

def test_update_upload_result(store, mock_db_instance):
    store.update_upload_result("t1", {"res": "ok"})
    args = mock_db_instance.execute_query_safe.call_args[0]
    assert "upload_result = %s" in args[0]

def test_update_error(store, mock_db_instance):
    store.update_error("t1", "failed")
    args = mock_db_instance.execute_query_safe.call_args[0]
    assert "error_message = %s" in args[0]
    assert "status = 'failed'" in args[0]

def test_list_tasks(store, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": "t1", "download_result": None}
    ]

    tasks = store.list_tasks(status="pending", username="u1", limit=10, offset=5)

    assert len(tasks) == 1
    args = mock_db_instance.fetch_query_safe.call_args[0]
    assert "status = %s" in args[0]
    assert "username = %s" in args[0]
    assert "LIMIT %s OFFSET %s" in args[0]
    assert args[1][0] == "pending"
    assert args[1][1] == "u1"
    assert args[1][2] == 10
    assert args[1][3] == 5

def test_list_tasks_failure(store, mock_db_instance):
    mock_db_instance.fetch_query_safe.side_effect = Exception("err")
    assert store.list_tasks() == []

def test_delete_task(store, mock_db_instance):
    assert store.delete_task("t1") is True
    mock_db_instance.execute_query_safe.assert_called_with(
        """
            DELETE FROM fix_nested_tasks WHERE id = %s
        """,
        ("t1",)
    )
