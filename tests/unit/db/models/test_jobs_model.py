from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, UniqueConstraint

from src.main_app.db.models.jobs import JobRecord


def test_job_record_initialization() -> None:
    """Test JobRecord initialization with required fields."""
    rec = JobRecord(id=1, job_type="copy_svg", username="testuser", status="pending")

    assert rec.id == 1
    assert rec.job_type == "copy_svg"
    assert rec.username == "testuser"
    assert rec.status == "pending"
    assert rec.started_at is None
    assert rec.completed_at is None
    assert rec.result_file is None
    assert rec.is_running is None


def test_job_record_with_all_fields() -> None:
    """Test JobRecord initialization with all fields."""
    dt = datetime(2025, 6, 1, 10, 30, 0)
    rec = JobRecord(
        id=10,
        job_type="rename_pages",
        username="admin",
        status="completed",
        started_at=dt,
        completed_at=dt,
        result_file="/path/to/result.json",
        created_at=dt,
        updated_at=dt,
        is_running=0,
    )

    assert rec.id == 10
    assert rec.job_type == "rename_pages"
    assert rec.username == "admin"
    assert rec.status == "completed"
    assert rec.started_at == dt
    assert rec.completed_at == dt
    assert rec.result_file == "/path/to/result.json"
    assert rec.created_at == dt
    assert rec.updated_at == dt
    assert rec.is_running == 0


def test_job_record_to_dict() -> None:
    """Test to_dict returns all expected keys with correct values."""
    dt = datetime(2025, 6, 1, 10, 30, 0)
    rec = JobRecord(
        id=5,
        job_type="copy_svg",
        username="bot",
        status="running",
        started_at=dt,
        completed_at=dt,
        result_file="output.csv",
        created_at=dt,
        updated_at=dt,
        is_running=1,
    )

    result = rec.to_dict()

    assert result["id"] == 5
    assert result["job_type"] == "copy_svg"
    assert result["username"] == "bot"
    assert result["status"] == "running"
    assert result["started_at"] == "2025-06-01T10:30:00"
    assert result["completed_at"] == "2025-06-01T10:30:00"
    assert result["result_file"] == "output.csv"
    assert result["created_at"] == "2025-06-01T10:30:00"
    assert result["updated_at"] == "2025-06-01T10:30:00"
    assert result["is_running"] == 1


def test_job_record_to_dict_handles_none() -> None:
    """Test to_dict correctly serializes None values."""
    rec = JobRecord(
        id=1,
        job_type="test",
        username="user",
        status="pending",
        started_at=None,
        completed_at=None,
        result_file=None,
        is_running=None,
    )

    result = rec.to_dict()

    assert result["started_at"] is None
    assert result["completed_at"] is None
    assert result["result_file"] is None
    assert result["is_running"] is None


def test_job_record_ignores_unknown_kwargs() -> None:
    """Test __init__ silently ignores unknown keyword arguments."""
    rec = JobRecord(id=1, job_type="test", username="user", status="pending", non_existent="ignored")

    assert rec.id == 1
    assert rec.job_type == "test"
    assert not hasattr(rec, "non_existent")


def test_job_record_table_name() -> None:
    """Test that JobRecord points to the 'jobs' table."""
    assert JobRecord.__tablename__ == "jobs"


def test_job_record_table_args() -> None:
    """Test that JobRecord has the expected unique constraint and index."""
    assert len(JobRecord.__table_args__) == 2

    unique_constraint = JobRecord.__table_args__[0]
    assert isinstance(unique_constraint, UniqueConstraint)
    assert unique_constraint.name == "idx_unique_active_job"
    assert tuple(c.key for c in unique_constraint.columns) == ("job_type", "is_running")

    index = JobRecord.__table_args__[1]
    assert isinstance(index, Index)
    assert index.name == "username"
    assert tuple(c.key for c in index.columns) == ("username",)
