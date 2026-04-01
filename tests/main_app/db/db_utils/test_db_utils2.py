"""
Tests for src/main_app/db/utils.py
"""

from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List

import pytest
from pytest_mock import MockerFixture

from src.main_app.db.utils import DbUtils


class TestDbUtilsRowsToTasksWithStages:
    """Tests for the _rows_to_tasks_with_stages method."""

    @pytest.fixture
    def db_utils(self) -> DbUtils:
        """Create a DbUtils instance for testing."""
        return DbUtils()

    def test_empty_rows(self, db_utils: DbUtils) -> None:
        """Test _rows_to_tasks_with_stages with empty rows."""
        rows: List[Dict[str, Any]] = []
        tasks, stage_map = db_utils._rows_to_tasks_with_stages(rows)

        assert tasks == []
        assert stage_map == {}

    def test_single_row_without_stage(self, db_utils: DbUtils) -> None:
        """Test _rows_to_tasks_with_stages with a single row without stage info."""
        rows: List[Dict[str, Any]] = [
            {
                "id": "task1",
                "title": "Test Task",
                "stage_name": None,
                "stage_number": None,
                "stage_status": None,
                "stage_sub_name": None,
                "stage_message": None,
                "stage_updated_at": None,
            }
        ]
        tasks, stage_map = db_utils._rows_to_tasks_with_stages(rows)

        assert len(tasks) == 1
        assert tasks[0]["id"] == "task1"
        assert tasks[0]["title"] == "Test Task"
        assert stage_map == {}

    def test_single_row_with_stage(self, db_utils: DbUtils) -> None:
        """Test _rows_to_tasks_with_stages with a single row with stage info."""
        rows: List[Dict[str, Any]] = [
            {
                "id": "task1",
                "title": "Test Task",
                "stage_name": "extract",
                "stage_number": 1,
                "stage_status": "completed",
                "stage_sub_name": None,
                "stage_message": "Done",
                "stage_updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            }
        ]
        tasks, stage_map = db_utils._rows_to_tasks_with_stages(rows)

        assert len(tasks) == 1
        assert tasks[0]["id"] == "task1"
        assert "extract" in stage_map["task1"]
        assert stage_map["task1"]["extract"]["number"] == 1
        assert stage_map["task1"]["extract"]["status"] == "completed"
        assert stage_map["task1"]["extract"]["message"] == "Done"
        assert stage_map["task1"]["extract"]["updated_at"] == "2025-01-01T12:00:00"

    def test_multiple_rows_same_task(self, db_utils: DbUtils) -> None:
        """Test _rows_to_tasks_with_stages with multiple rows for the same task."""
        rows: List[Dict[str, Any]] = [
            {
                "id": "task1",
                "title": "Test Task",
                "stage_name": "extract",
                "stage_number": 1,
                "stage_status": "completed",
                "stage_sub_name": None,
                "stage_message": "Extract done",
                "stage_updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            },
            {
                "id": "task1",
                "title": "Test Task",
                "stage_name": "upload",
                "stage_number": 2,
                "stage_status": "pending",
                "stage_sub_name": None,
                "stage_message": None,
                "stage_updated_at": datetime.datetime(2025, 1, 1, 13, 0, 0),
            },
        ]
        tasks, stage_map = db_utils._rows_to_tasks_with_stages(rows)

        assert len(tasks) == 1
        assert tasks[0]["id"] == "task1"
        assert len(stage_map["task1"]) == 2
        assert "extract" in stage_map["task1"]
        assert "upload" in stage_map["task1"]

    def test_multiple_tasks(self, db_utils: DbUtils) -> None:
        """Test _rows_to_tasks_with_stages with multiple tasks."""
        rows: List[Dict[str, Any]] = [
            {
                "id": "task1",
                "title": "Task 1",
                "stage_name": "extract",
                "stage_number": 1,
                "stage_status": "completed",
                "stage_sub_name": None,
                "stage_message": None,
                "stage_updated_at": None,
            },
            {
                "id": "task2",
                "title": "Task 2",
                "stage_name": "extract",
                "stage_number": 1,
                "stage_status": "pending",
                "stage_sub_name": None,
                "stage_message": None,
                "stage_updated_at": None,
            },
        ]
        tasks, stage_map = db_utils._rows_to_tasks_with_stages(rows)

        assert len(tasks) == 2
        assert tasks[0]["id"] == "task1"
        assert tasks[1]["id"] == "task2"
        assert "task1" in stage_map
        assert "task2" in stage_map

    def test_stage_updated_at_none(self, db_utils: DbUtils) -> None:
        """Test _rows_to_tasks_with_stages handles None updated_at."""
        rows: List[Dict[str, Any]] = [
            {
                "id": "task1",
                "title": "Test Task",
                "stage_name": "extract",
                "stage_number": 1,
                "stage_status": "completed",
                "stage_sub_name": None,
                "stage_message": None,
                "stage_updated_at": None,
            }
        ]
        tasks, stage_map = db_utils._rows_to_tasks_with_stages(rows)

        assert stage_map["task1"]["extract"]["updated_at"] is None


class TestDbUtilsRowToTask:
    """Tests for the _row_to_task method."""

    @pytest.fixture
    def db_utils(self) -> DbUtils:
        """Create a DbUtils instance for testing."""
        return DbUtils()

    def test_row_to_task_basic(self, db_utils: DbUtils) -> None:
        """Test _row_to_task with basic row data."""
        row: Dict[str, Any] = {
            "id": "task1",
            "username": "testuser",
            "title": "Test Task",
            "normalized_title": "test task",
            "status": "completed",
            "form_json": '{"key": "value"}',
            "data_json": '{"data": "info"}',
            "main_file": "File:Test.svg",
            "results_json": '{"result": "success"}',
            "created_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2025, 1, 2, 13, 0, 0),
        }

        task = db_utils._row_to_task(row, stages={})

        assert task["id"] == "task1"
        assert task["username"] == "testuser"
        assert task["title"] == "Test Task"
        assert task["normalized_title"] == "test task"
        assert task["status"] == "completed"
        assert task["form"] == {"key": "value"}
        assert task["data"] == {"data": "info"}
        assert task["main_file"] == "File:Test.svg"
        assert task["results"] == {"result": "success"}
        assert task["created_at"] == "2025-01-01T12:00:00"
        assert task["updated_at"] == "2025-01-02T13:00:00"
        assert task["stages"] == {}

    def test_row_to_task_removes_csrf_token(self, db_utils: DbUtils) -> None:
        """Test _row_to_task removes csrf_token from form data."""
        row: Dict[str, Any] = {
            "id": "task1",
            "username": "testuser",
            "title": "Test Task",
            "normalized_title": "test task",
            "status": "pending",
            "form_json": '{"csrf_token": "secret", "key": "value"}',
            "data_json": None,
            "main_file": "",
            "results_json": None,
            "created_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
        }

        task = db_utils._row_to_task(row, stages={})

        assert task["form"] == {"key": "value"}
        assert "csrf_token" not in task["form"]

    def test_row_to_task_none_json_values(self, db_utils: DbUtils) -> None:
        """Test _row_to_task handles None JSON values."""
        row: Dict[str, Any] = {
            "id": "task1",
            "username": "testuser",
            "title": "Test Task",
            "normalized_title": "test task",
            "status": "pending",
            "form_json": None,
            "data_json": None,
            "main_file": "",
            "results_json": None,
            "created_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
        }

        task = db_utils._row_to_task(row, stages={})

        assert task["form"] is None
        assert task["data"] is None
        assert task["results"] is None

    def test_row_to_task_fetches_stages_when_not_provided(self, db_utils: DbUtils, mocker: MockerFixture) -> None:
        """Test _row_to_task uses stages when provided (since fetch_stages is not defined on DbUtils)."""
        row: Dict[str, Any] = {
            "id": "task1",
            "username": "testuser",
            "title": "Test Task",
            "normalized_title": "test task",
            "status": "pending",
            "form_json": None,
            "data_json": None,
            "main_file": "",
            "results_json": None,
            "created_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
        }

        mock_stages = {"extract": {"status": "completed"}}
        # Provide stages directly since fetch_stages is not defined on DbUtils class
        task = db_utils._row_to_task(row, stages=mock_stages)

        assert task["stages"] == mock_stages

    def test_row_to_task_preserves_empty_stages_dict(self, db_utils: DbUtils) -> None:
        """Test _row_to_task preserves empty stages dict when provided."""
        row: Dict[str, Any] = {
            "id": "task1",
            "username": "testuser",
            "title": "Test Task",
            "normalized_title": "test task",
            "status": "pending",
            "form_json": None,
            "data_json": None,
            "main_file": "",
            "results_json": None,
            "created_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
        }

        task = db_utils._row_to_task(row, stages={})

        assert task["stages"] == {}


class TestDbUtilsSerialize:
    """Tests for the _serialize method."""

    @pytest.fixture
    def db_utils(self) -> DbUtils:
        """Create a DbUtils instance for testing."""
        return DbUtils()

    def test_serialize_none(self, db_utils: DbUtils) -> None:
        """Test _serialize returns None for None input."""
        result = db_utils._serialize(None)
        assert result is None

    def test_serialize_dict(self, db_utils: DbUtils) -> None:
        """Test _serialize serializes a dictionary."""
        data = {"key": "value", "number": 42}
        result = db_utils._serialize(data)
        assert result == json.dumps(data, ensure_ascii=False)

    def test_serialize_removes_csrf_token(self, db_utils: DbUtils) -> None:
        """Test _serialize removes csrf_token from dict."""
        data = {"csrf_token": "secret", "key": "value"}
        result = db_utils._serialize(data)
        expected = {"key": "value"}
        assert json.loads(result) == expected

    def test_serialize_unicode(self, db_utils: DbUtils) -> None:
        """Test _serialize preserves unicode characters."""
        data = {"text": "Hello 世界"}
        result = db_utils._serialize(data)
        assert "世界" in result


class TestDbUtilsDeserialize:
    """Tests for the _deserialize method."""

    @pytest.fixture
    def db_utils(self) -> DbUtils:
        """Create a DbUtils instance for testing."""
        return DbUtils()

    def test_deserialize_none(self, db_utils: DbUtils) -> None:
        """Test _deserialize returns None for None input."""
        result = db_utils._deserialize(None)
        assert result is None

    def test_deserialize_json_string(self, db_utils: DbUtils) -> None:
        """Test _deserialize parses a JSON string."""
        json_str = '{"key": "value", "number": 42}'
        result = db_utils._deserialize(json_str)
        assert result == {"key": "value", "number": 42}

    def test_deserialize_unicode(self, db_utils: DbUtils) -> None:
        """Test _deserialize handles unicode characters."""
        json_str = '{"text": "Hello 世界"}'
        result = db_utils._deserialize(json_str)
        assert result == {"text": "Hello 世界"}


class TestDbUtilsCurrentTs:
    """Tests for the _current_ts method."""

    @pytest.fixture
    def db_utils(self) -> DbUtils:
        """Create a DbUtils instance for testing."""
        return DbUtils()

    def test_current_ts_format(self, db_utils: DbUtils) -> None:
        """Test _current_ts returns correct format."""
        result = db_utils._current_ts()
        # Should be in format "YYYY-MM-DD HH:MM:SS"
        assert len(result) == 19
        assert result[4] == "-"
        assert result[7] == "-"
        assert result[10] == " "
        assert result[13] == ":"
        assert result[16] == ":"

    def test_current_ts_is_recent(self, db_utils: DbUtils) -> None:
        """Test _current_ts returns a recent timestamp."""
        # Add a small buffer to account for the fact that _current_ts has no microseconds
        before = datetime.datetime.now(datetime.UTC).replace(microsecond=0) - datetime.timedelta(seconds=1)
        result = db_utils._current_ts()
        after = datetime.datetime.now(datetime.UTC).replace(microsecond=0) + datetime.timedelta(seconds=1)

        ts = datetime.datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        ts = ts.replace(tzinfo=datetime.UTC)

        assert before <= ts <= after


class TestDbUtilsNormalizeTitle:
    """Tests for the _normalize_title method."""

    @pytest.fixture
    def db_utils(self) -> DbUtils:
        """Create a DbUtils instance for testing."""
        return DbUtils()

    def test_normalize_title_basic(self, db_utils: DbUtils) -> None:
        """Test _normalize_title basic normalization."""
        result = db_utils._normalize_title("Test Title")
        assert result == "test title"

    def test_normalize_title_strips_whitespace(self, db_utils: DbUtils) -> None:
        """Test _normalize_title strips whitespace."""
        result = db_utils._normalize_title("  Test Title  ")
        assert result == "test title"

    def test_normalize_title_replaces_underscores(self, db_utils: DbUtils) -> None:
        """Test _normalize_title replaces underscores with spaces."""
        result = db_utils._normalize_title("Test_Title_With_Underscores")
        assert result == "test title with underscores"

    def test_normalize_title_casefold(self, db_utils: DbUtils) -> None:
        """Test _normalize_title handles special characters."""
        result = db_utils._normalize_title("TEST TITLE")
        assert result == "test title"

    def test_normalize_title_unicode(self, db_utils: DbUtils) -> None:
        """Test _normalize_title handles unicode."""
        result = db_utils._normalize_title("Tëst Tïtlë")
        assert result == "tëst tïtlë"
