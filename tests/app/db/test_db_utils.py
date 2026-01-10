import pytest
import json
import datetime
from unittest.mock import MagicMock
from src.app.db.utils import DbUtils

class MockDbUtils(DbUtils):
    def fetch_stages(self, task_id):
        return {"mock_stage": {}}

def test_serialize_deserialize():
    utils = DbUtils()
    data = {"key": "value", "list": [1, 2]}
    serialized = utils._serialize(data)
    assert isinstance(serialized, str)
    assert utils._deserialize(serialized) == data
    
    assert utils._serialize(None) is None
    assert utils._deserialize(None) is None

def test_normalize_title():
    utils = DbUtils()
    assert utils._normalize_title("  Test_Title  ") == "test title"
    assert utils._normalize_title("My Title") == "my title"

def test_current_ts():
    utils = DbUtils()
    ts = utils._current_ts()
    # Format: YYYY-MM-DD HH:MM:SS
    assert len(ts) == 19
    assert ts[4] == "-" and ts[7] == "-" and ts[10] == " "
    assert ts[13] == ":" and ts[16] == ":"

def test_rows_to_tasks_with_stages():
    utils = DbUtils()
    
    # Mock datetime
    now = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    rows = [
        # Task 1, Stage 1
        {
            "id": "t1", "title": "Task 1", "stage_name": "s1", 
            "stage_number": 1, "stage_status": "done", 
            "stage_sub_name": None, "stage_message": "ok", 
            "stage_updated_at": now
        },
        # Task 1, Stage 2
        {
            "id": "t1", "title": "Task 1", "stage_name": "s2", 
            "stage_number": 2, "stage_status": "pending", 
            "stage_sub_name": None, "stage_message": None, 
            "stage_updated_at": "2023-01-01 13:00:00"
        },
        # Task 2, No stages
        {
            "id": "t2", "title": "Task 2", "stage_name": None
        }
    ]
    
    tasks, stage_map = utils._rows_to_tasks_with_stages(rows)
    
    assert len(tasks) == 2
    # Order should be preserved from rows encounter
    assert tasks[0]["id"] == "t1"
    assert tasks[1]["id"] == "t2"
    
    assert "t1" in stage_map
    assert "s1" in stage_map["t1"]
    assert "s2" in stage_map["t1"]
    assert stage_map["t1"]["s1"]["status"] == "done"
    assert stage_map["t1"]["s1"]["updated_at"] == now.isoformat()
    assert stage_map["t1"]["s2"]["updated_at"] == "2023-01-01 13:00:00"
    
    assert "t2" not in stage_map

def test_row_to_task():
    utils = MockDbUtils() 
    
    now = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    row = {
        "id": "t1",
        "title": "Task 1",
        "normalized_title": "task 1",
        "status": "pending",
        "form_json": '{"f": 1}',
        "data_json": None,
        "results_json": None,
        "created_at": now,
        "updated_at": now,
        "main_file": "file.svg",
        "username": "user"
    }
    
    # 1. With stages provided
    stages = {"s1": {}}
    task = utils._row_to_task(row, stages=stages)
    assert task["form"] == {"f": 1}
    assert task["stages"] == stages
    assert task["created_at"] == now.isoformat()
    
    # 2. Without stages (uses fetch_stages)
    task2 = utils._row_to_task(row)
    assert task2["stages"] == {"mock_stage": {}}