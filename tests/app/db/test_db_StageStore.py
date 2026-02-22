from unittest.mock import MagicMock

import pytest

from src.main_app.db.db_StageStore import StageStore


class MockStageStore(StageStore):
    def _current_ts(self):
        return "2023-01-01 12:00:00"


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def stage_store(mock_db):
    store = MockStageStore(db=mock_db)
    return store


def test_update_stage_success(stage_store, mock_db):
    stage_data = {"number": 1, "status": "In Progress", "sub_name": "sub", "message": "msg"}

    stage_store.update_stage("t1", "stage1", stage_data)

    mock_db.execute_query.assert_called()
    query, params = mock_db.execute_query.call_args[0]

    assert "INSERT INTO task_stages" in query
    assert params[0] == "t1:stage1"
    assert params[1] == "t1"
    assert params[2] == "stage1"
    assert params[3] == 1
    assert params[4] == "In Progress"
    assert params[5] == "sub"
    assert params[6] == "msg"
    assert params[7] == "2023-01-01 12:00:00"


def test_update_stage_exception(stage_store, mock_db):
    mock_db.execute_query.side_effect = Exception("db error")
    # Should log error and not raise
    stage_store.update_stage("t1", "stage1", {})


def test_update_stage_column_allowed(stage_store, mock_db):
    stage_store.update_stage_column("t1", "stage1", "stage_status", "Done")

    mock_db.execute_query.assert_called()
    query, params = mock_db.execute_query.call_args[0]

    assert "UPDATE task_stages SET stage_status = %s" in query
    assert params[0] == "Done"
    assert params[2] == "t1:stage1"


def test_update_stage_column_not_allowed(stage_store, mock_db):
    stage_store.update_stage_column("t1", "stage1", "invalid_col", "val")
    # Should return early
    mock_db.execute_query.assert_not_called()


def test_update_stage_column_exception(stage_store, mock_db):
    mock_db.execute_query.side_effect = Exception("db error")
    # Should log error and not raise
    stage_store.update_stage_column("t1", "stage1", "stage_status", "val")


def test_fetch_stages_success(stage_store, mock_db):
    mock_db.fetch_query_safe.return_value = [
        {
            "stage_name": "s1",
            "stage_number": 1,
            "stage_status": "done",
            "stage_sub_name": None,
            "stage_message": "ok",
            "updated_at": "2023-01-01 10:00:00",
        }
    ]

    stages = stage_store.fetch_stages("t1")

    assert "s1" in stages
    assert stages["s1"]["number"] == 1
    assert stages["s1"]["status"] == "done"
    assert stages["s1"]["updated_at"] == "2023-01-01 10:00:00"


def test_fetch_stages_empty(stage_store, mock_db):
    mock_db.fetch_query_safe.return_value = []

    stages = stage_store.fetch_stages("t1")
    assert stages == {}


def test_fetch_stages_datetime_formatting(stage_store, mock_db):
    # Mock datetime object
    dt = MagicMock()
    dt.isoformat.return_value = "ISO-DATE"

    mock_db.fetch_query_safe.return_value = [
        {
            "stage_name": "s1",
            "stage_number": 1,
            "stage_status": "done",
            "stage_sub_name": None,
            "stage_message": None,
            "updated_at": dt,
        }
    ]

    stages = stage_store.fetch_stages("t1")
    assert stages["s1"]["updated_at"] == "ISO-DATE"
