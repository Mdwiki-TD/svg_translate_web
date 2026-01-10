import pytest
from unittest.mock import MagicMock
from src.app.db.db_TasksListDB import TasksListDB
from src.app.db.utils import DbUtils

class MockTasksListDB(TasksListDB, DbUtils):
    def fetch_stages(self, task_id):
        return {}

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def tasks_db(mock_db):
    return MockTasksListDB(db=mock_db)

def test_create_base_sql_simple(tasks_db):
    query_parts, params = tasks_db.create_base_sql(
        order_column="created_at",
        statuses=None,
        status=None,
        username=None,
        direction="DESC",
        limit=None,
        offset=None
    )
    sql = " ".join(query_parts)
    assert "SELECT * FROM tasks" in sql
    assert "ORDER BY created_at DESC" in sql
    assert "WHERE" not in sql
    assert "LIMIT" not in sql
    assert params == []

def test_create_base_sql_filtered(tasks_db):
    query_parts, params = tasks_db.create_base_sql(
        order_column="title",
        statuses=["pending"],
        status="failed",
        username="user1",
        direction="ASC",
        limit=10,
        offset=5
    )
    sql = " ".join(query_parts)
    assert "status IN (%s, %s)" in sql
    assert "username = %s" in sql
    assert "ORDER BY title ASC" in sql
    assert "LIMIT %s" in sql
    assert "OFFSET %s" in sql
    
    # Check params order
    # statuses + status first, then username, then limit, then offset
    assert params[0] == "pending"
    assert params[1] == "failed"
    assert params[2] == "user1"
    assert params[3] == 10
    assert params[4] == 5

def test_list_tasks_success(tasks_db, mock_db):
    # Mock return from fetch_query_safe
    # It should return joined rows (task + stage)
    mock_db.fetch_query_safe.return_value = [
        {
            "id": "t1", "title": "Task 1", "status": "done",
            "created_at": "2023-01-01", "updated_at": "2023-01-01",
            "normalized_title": "task 1", "form_json": None, "data_json": None, "results_json": None,
            "stage_name": "s1", "stage_number": 1, "stage_status": "done",
            "stage_sub_name": None, "stage_message": None, "stage_updated_at": None,
            "main_file": "f.svg" # Added to match _row_to_task expectations if strictly typed or accessed
        }
    ]
    
    tasks = tasks_db.list_tasks(limit=10)
    
    assert len(tasks) == 1
    assert tasks[0]["id"] == "t1"
    assert tasks[0]["stages"]["s1"]["status"] == "done"
    
    # Verify SQL query structure
    args = mock_db.fetch_query_safe.call_args[0]
    sql = args[0]
    assert "SELECT * FROM tasks" in sql
    assert "LEFT JOIN task_stages" in sql
    assert "ORDER BY t.created_at DESC" in sql

def test_list_tasks_no_results(tasks_db, mock_db):
    mock_db.fetch_query_safe.return_value = []
    tasks = tasks_db.list_tasks()
    assert tasks == []

def test_list_tasks_db_failure(tasks_db, mock_db):
    mock_db.fetch_query_safe.return_value = [] 
    # Technically fetch_query_safe returns [] on error too, but handled same way
    tasks = tasks_db.list_tasks()
    assert tasks == []

def test_offset_without_limit(tasks_db):
    # Special case where offset requires a limit
    query_parts, params = tasks_db.create_base_sql(
        "created_at", None, None, None, "DESC", None, 5
    )
    sql = " ".join(query_parts)
    # Check for large limit constant
    assert "LIMIT 18446744073709551615" in sql
    assert "OFFSET %s" in sql
    assert params[-1] == 5