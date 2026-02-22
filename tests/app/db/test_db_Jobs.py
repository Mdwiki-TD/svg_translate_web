import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.main_app.db.db_Jobs import JobsDB, JobRecord


@pytest.fixture
def mock_db_class(mocker):
    return mocker.patch("src.main_app.db.db_Jobs.Database")


@pytest.fixture
def mock_db_instance(mock_db_class):
    instance = MagicMock()
    mock_db_class.return_value = instance
    return instance


@pytest.fixture
def jobs_db(mock_db_instance):
    return JobsDB({})


def test_JobRecord():
    now = datetime.now()
    record = JobRecord(
        id=1,
        job_type="test",
        status="pending",
        created_at=now
    )
    assert record.id == 1
    assert record.job_type == "test"
    assert record.status == "pending"
    assert record.created_at == now
    assert record.started_at is None


def test_ensure_table(mock_db_instance):
    JobsDB({})
    mock_db_instance.execute_query_safe.assert_called()
    assert "CREATE TABLE IF NOT EXISTS jobs" in mock_db_instance.execute_query_safe.call_args[0][0]


def test_create_success(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1,
        "job_type": "type_a",
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "result_file": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }]

    record = jobs_db.create("type_a")

    mock_db_instance.execute_query_safe.assert_called_with(
        "\n            INSERT INTO jobs (job_type, status) VALUES (%s, %s)\n            ",
        ("type_a", "pending")
    )
    assert record.id == 1
    assert record.job_type == "type_a"


def test_create_failure(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = []
    with pytest.raises(RuntimeError, match="Failed to create job"):
        jobs_db.create("type_a")


def test_get_success(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1,
        "job_type": "type_a",
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "result_file": None,
        "created_at": None,
        "updated_at": None
    }]

    record = jobs_db.get(1, "type_a")
    assert record.id == 1
    assert record.status == "pending"


def test_get_not_found(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = []
    with pytest.raises(LookupError, match="not found"):
        jobs_db.get(1, "type_a")


def test_list_all(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "job_type": "t1", "status": "pending"},
        {"id": 2, "job_type": "t2", "status": "completed"}
    ]

    records = jobs_db.list()
    assert len(records) == 2
    mock_db_instance.fetch_query_safe.assert_called()
    args = mock_db_instance.fetch_query_safe.call_args[0]
    assert "WHERE job_type =" not in args[0]  # Should not filter by type


def test_list_filtered(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = []
    jobs_db.list(job_type="specific")
    args = mock_db_instance.fetch_query_safe.call_args[0]
    assert "WHERE job_type = %s" in args[0]
    assert args[1][0] == "specific"


def test_delete_success(jobs_db, mock_db_instance):
    assert jobs_db.delete(1, "type") is True
    mock_db_instance.execute_query_safe.assert_called()


def test_delete_exception(jobs_db, mock_db_instance):
    mock_db_instance.execute_query_safe.side_effect = Exception("db error")
    assert jobs_db.delete(1, "type") is False


def test_update_status_running(jobs_db, mock_db_instance):
    # Setup for get() call inside update_status
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1, "job_type": "t", "status": "running"
    }]
    mock_db_instance.execute_query_safe.return_value = 1  # One row updated

    record = jobs_db.update_status(1, "running", job_type="t")

    mock_db_instance.execute_query_safe.assert_called()
    call_args = mock_db_instance.execute_query_safe.call_args
    assert "UPDATE jobs SET status = %s, started_at = NOW()" in call_args[0][0]
    assert "running" in call_args[0][1]
    assert record.status == "running"


def test_update_status_completed(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1, "job_type": "t", "status": "completed"
    }]
    mock_db_instance.execute_query_safe.return_value = 1

    jobs_db.update_status(1, "completed", result_file="res.json", job_type="t")

    call_args = mock_db_instance.execute_query_safe.call_args
    assert "completed_at = NOW()" in call_args[0][0]
    assert "result_file = %s" in call_args[0][0]
    assert "res.json" in call_args[0][1]


def test_update_status_generic(jobs_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1, "job_type": "t", "status": "other"
    }]
    mock_db_instance.execute_query_safe.return_value = 1

    jobs_db.update_status(1, "other", job_type="t")

    call_args = mock_db_instance.execute_query_safe.call_args
    assert "completed_at" not in call_args[0][0]
    assert "started_at" not in call_args[0][0]


def test_update_status_not_found(jobs_db, mock_db_instance):
    mock_db_instance.execute_query_safe.return_value = 0  # No rows updated

    with pytest.raises(LookupError):
        jobs_db.update_status(1, "running")


def test_update_status_with_result_file_on_running(jobs_db, mock_db_instance):
    """Test update_status with result_file parameter when status is running."""
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1, "job_type": "t", "status": "running"
    }]
    mock_db_instance.execute_query_safe.return_value = 1

    jobs_db.update_status(1, "running", result_file="partial.json", job_type="t")

    call_args = mock_db_instance.execute_query_safe.call_args
    assert "result_file = %s" in call_args[0][0]
    assert "partial.json" in call_args[0][1]


def test_update_status_failed(jobs_db, mock_db_instance):
    """Test update_status with 'failed' status."""
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1, "job_type": "t", "status": "failed"
    }]
    mock_db_instance.execute_query_safe.return_value = 1

    jobs_db.update_status(1, "failed", result_file="error.json", job_type="t")

    call_args = mock_db_instance.execute_query_safe.call_args
    assert "completed_at = NOW()" in call_args[0][0]
    assert "result_file = %s" in call_args[0][0]


def test_update_status_cancelled(jobs_db, mock_db_instance):
    """Test update_status with 'cancelled' status."""
    mock_db_instance.fetch_query_safe.return_value = [{
        "id": 1, "job_type": "t", "status": "cancelled"
    }]
    mock_db_instance.execute_query_safe.return_value = 1

    jobs_db.update_status(1, "cancelled", job_type="t")

    call_args = mock_db_instance.execute_query_safe.call_args
    assert "completed_at = NOW()" in call_args[0][0]


def test_list_with_limit(jobs_db, mock_db_instance):
    """Test list method with custom limit."""
    mock_db_instance.fetch_query_safe.return_value = []

    jobs_db.list(limit=50)

    call_args = mock_db_instance.fetch_query_safe.call_args
    assert 50 in call_args[0][1]


def test_row_to_record_with_all_fields(jobs_db):
    """Test _row_to_record with all fields populated."""
    now = datetime.now()
    row = {
        "id": 42,
        "job_type": "test_type",
        "status": "completed",
        "started_at": now,
        "completed_at": now,
        "result_file": "result.json",
        "created_at": now,
        "updated_at": now
    }

    record = jobs_db._row_to_record(row)

    assert record.id == 42
    assert record.job_type == "test_type"
    assert record.status == "completed"
    assert record.started_at == now
    assert record.completed_at == now
    assert record.result_file == "result.json"
    assert record.created_at == now
    assert record.updated_at == now
