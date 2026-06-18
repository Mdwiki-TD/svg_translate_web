"""Unit tests for jobs_service module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from src.main_app.db.models import JobRecord
from src.main_app.db.services.delete_service import delete_job
from src.main_app.db.services.jobs_service import (
    _normalize_limit,
    cancel_job_db,
    create_job,
    get_all_user_jobs_stats,
    get_job,
    get_user_jobs_stats,
    has_active_job,
    is_job_cancelled,
    list_jobs,
    update_job_status,
)


def test_create_job():
    """Test creating a new job."""
    job = create_job("collect_templates_data", username="test_user")

    assert job is not None
    assert job.id == 1
    assert job.job_type == "collect_templates_data"
    assert job.status == "pending"


def test_create_job_with_username():
    """Test creating a new job with username."""
    job = create_job("collect_templates_data", username="test_user")

    assert job is not None
    assert job.id == 1
    assert job.job_type == "collect_templates_data"
    assert job.status == "pending"
    assert job.username == "test_user"


def test_get_job():
    """Test retrieving a job by ID."""
    created_job = create_job("collect_templates_data", username="z")

    retrieved_job = get_job(created_job.id, job_type="collect_templates_data")

    assert retrieved_job.id == created_job.id
    assert retrieved_job.job_type == created_job.job_type


def test_get_nonexistent_job():
    """Test retrieving a nonexistent job raises LookupError."""
    with pytest.raises(LookupError, match="Job id 999 was not found"):
        get_job(999, job_type="collect_templates_data")


def test_list_jobs():
    """Test listing jobs."""
    job1 = create_job("collect_templates_data", username="z")
    update_job_status(job1.id, "completed", job_type="collect_templates_data")
    create_job("collect_templates_data", username="z")
    create_job("other_job", username="z")

    jobs = list_jobs()

    assert len(jobs) == 3
    assert all(isinstance(job, JobRecord) for job in jobs)


def test_list_jobs_with_limit():
    """Test listing jobs with a limit."""
    for i in range(5):
        job = create_job("collect_templates_data", username="z")
        if i < 4:
            update_job_status(job.id, "completed", job_type="collect_templates_data")

    jobs = list_jobs(limit=2)

    assert len(jobs) == 2


def test_update_job_status():
    """Test updating a job's status."""
    job = create_job("collect_templates_data", username="z")

    updated_job = update_job_status(job.id, "running", job_type="collect_templates_data")

    assert updated_job.status == "running"


def test_update_job_status_with_result_file():
    """Test updating a job's status with a result file."""
    job = create_job("collect_templates_data", username="z")

    updated_job = update_job_status(job.id, "completed", "/path/to/result.json", job_type="collect_templates_data")

    assert updated_job.status == "completed"
    assert updated_job.result_file == "/path/to/result.json"


def test_delete_job():
    """Test deleting a job."""
    job = create_job("collect_templates_data", username="z")
    assert len(list_jobs()) == 1

    delete_job(job.id, "collect_templates_data")
    jobs_len = len(list_jobs())
    assert jobs_len == 0


def test_delete_job_with_correct_type():
    """Test deleting a job with correct job type."""
    job1 = create_job("collect_templates_data", username="z")
    job2 = create_job("fix_nested_main_files", username="z")
    assert len(list_jobs()) == 2

    delete_job(job1.id, "collect_templates_data")

    remaining_jobs = list_jobs()
    assert len(remaining_jobs) == 1
    assert remaining_jobs[0].id == job2.id


def test_delete_job_with_wrong_type():
    """Test deleting a job with wrong job type doesn't delete it."""
    job = create_job("collect_templates_data", username="z")
    assert len(list_jobs()) == 1

    # Try to delete with wrong job type
    delete_job(job.id, "fix_nested_main_files")

    # Job should still exist
    remaining_jobs = list_jobs()
    assert len(remaining_jobs) == 1
    assert remaining_jobs[0].id == job.id


def test_delete_nonexistent_job():
    """Test deleting a non-existent job."""
    # Should not raise an error
    delete_job(999, "collect_templates_data")

    # No jobs should exist
    assert len(list_jobs()) == 0


def test_list_jobs_filtered_by_type():
    """Test listing jobs filtered by job_type."""
    job1 = create_job("collect_templates_data", username="z")
    update_job_status(job1.id, "completed", job_type="collect_templates_data")
    create_job("collect_templates_data", username="z")
    create_job("fix_nested_main_files", username="z")
    create_job("other_job_type", username="z")

    # Filter by collect_templates_data
    collect_jobs = list_jobs(job_type="collect_templates_data")
    assert len(collect_jobs) == 2
    assert all(job.job_type == "collect_templates_data" for job in collect_jobs)

    # Filter by fix_nested_main_files
    fix_jobs = list_jobs(job_type="fix_nested_main_files")
    assert len(fix_jobs) == 1
    assert all(job.job_type == "fix_nested_main_files" for job in fix_jobs)

    # No filter - should return all
    all_jobs = list_jobs()
    assert len(all_jobs) == 4


def test_list_jobs_filtered_with_limit():
    """Test listing jobs filtered by job_type with a limit."""
    for i in range(5):
        job = create_job("collect_templates_data", username="z")
        if i < 4:
            update_job_status(job.id, "completed", job_type="collect_templates_data")
    for i in range(3):
        job = create_job("fix_nested_main_files", username="z")
        if i < 2:
            update_job_status(job.id, "completed", job_type="fix_nested_main_files")

    # Filter by type with limit
    collect_jobs = list_jobs(limit=2, job_type="collect_templates_data")
    assert len(collect_jobs) == 2
    assert all(job.job_type == "collect_templates_data" for job in collect_jobs)


def test_update_job_status_nonexistent():
    """Test updating status of a nonexistent job raises LookupError."""
    with pytest.raises(LookupError):
        update_job_status(999, "completed", job_type="test_job")


# ── Normalization ──


class TestNormalizeLimit:
    """Tests for _normalize_limit helper."""

    def test_returns_default_when_none(self):
        assert _normalize_limit(None) == 100

    def test_returns_default_when_zero_or_negative(self):
        assert _normalize_limit(0) == 100
        assert _normalize_limit(-1) == 100
        assert _normalize_limit(-100) == 100

    def test_caps_at_max_limit(self):
        assert _normalize_limit(1000) == 500
        assert _normalize_limit(501) == 500

    def test_returns_limit_when_within_range(self):
        assert _normalize_limit(50) == 50
        assert _normalize_limit(100) == 100
        assert _normalize_limit(500) == 500


# ── Status queries ──


class TestIsJobCancelled:
    """Tests for is_job_cancelled."""

    def test_cancelled_status_returns_true(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.status = "cancelled"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.refresh", lambda x: None)
        result = is_job_cancelled(1, "test")
        assert result is True

    def test_active_statuses_return_false(self, monkeypatch):
        for status in ("pending", "running", "completed"):
            mock_record = MagicMock()
            mock_record.status = status
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = mock_record
            monkeypatch.setattr(
                "src.main_app.db.services.jobs_service.db.session.query", lambda cls, _mock=mock_query: _mock
            )
            monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.refresh", lambda x: None)
            result = is_job_cancelled(1, "test")
            assert result is False

    def test_no_record_returns_false(self, monkeypatch):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", lambda cls: mock_query)
        result = is_job_cancelled(1, "test")
        assert result is False

    def test_refresh_called_before_checking_status(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.status = "cancelled"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        refresh = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.refresh", refresh)
        is_job_cancelled(1, "test")
        refresh.assert_called_once_with(mock_record)


class TestGetJob:
    """Tests for get_job."""

    def test_returns_job_when_found(self):
        job = create_job("test_job", username="test_user")
        result = get_job(job.id, "test_job")
        assert result.id == job.id
        assert result.job_type == "test_job"

    def test_raises_lookup_error_when_not_found(self):
        with pytest.raises(LookupError, match="Job id 999 was not found"):
            get_job(999, "test_job")


class TestListJobs:
    """Tests for list_jobs."""

    def test_empty_list_when_no_jobs(self):
        jobs = list_jobs()
        assert jobs == []


# ── User stats ──


class TestGetAllUserJobsStats:
    """Tests for get_all_user_jobs_stats."""

    def test_returns_stats_with_correct_counts(self, monkeypatch):
        mock_group_records = [("completed", 5), ("failed", 2)]
        mock_group_query = MagicMock()
        mock_group_query.filter.return_value.group_by.return_value.all.return_value = mock_group_records

        mock_recent_jobs = [MagicMock(id=1)]
        mock_base_query = MagicMock()
        mock_base_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_recent_jobs

        call_count = [0]

        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_base_query
            return mock_group_query

        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", query_side_effect)
        result = get_all_user_jobs_stats("test_user")
        assert result["stats"]["total"] == 7
        assert result["stats"]["completed"] == 5
        assert result["stats"]["failed"] == 2

    def test_handles_empty_records(self, monkeypatch):
        mock_group_query = MagicMock()
        mock_group_query.filter.return_value.group_by.return_value.all.return_value = []

        mock_base_query = MagicMock()
        mock_base_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        call_count = [0]

        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_base_query
            return mock_group_query

        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", query_side_effect)
        result = get_all_user_jobs_stats("test_user")
        assert result["stats"]["total"] == 0
        assert result["stats"]["completed"] == 0
        assert result["stats"]["failed"] == 0
        assert result["recent_jobs"] == []

    def test_respects_limit_parameter(self, monkeypatch):
        mock_group_records = [("completed", 3)]
        mock_group_query = MagicMock()
        mock_group_query.filter.return_value.group_by.return_value.all.return_value = mock_group_records

        mock_base_query = MagicMock()
        mock_base_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            MagicMock(id=1)
        ]

        call_count = [0]

        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_base_query
            return mock_group_query

        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", query_side_effect)
        result = get_all_user_jobs_stats("test_user", limit=5)
        assert result["stats"]["total"] == 3
        assert result["stats"]["completed"] == 3
        assert len(result["recent_jobs"]) == 1


class TestGetUserJobsStats:
    """Tests for get_user_jobs_stats."""

    def test_with_jobs_types_filters_correctly(self, monkeypatch):
        mock_group_records = [("completed", 2)]
        mock_group_query = MagicMock()
        mock_group_query.filter.return_value.filter.return_value.group_by.return_value.all.return_value = (
            mock_group_records
        )

        mock_base_query = MagicMock()
        mock_base_query.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            MagicMock(id=1)
        ]

        call_count = [0]

        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_base_query
            return mock_group_query

        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", query_side_effect)
        result = get_user_jobs_stats("test_user", jobs_types=["type_a", "type_b"])
        assert result["stats"]["total"] == 2
        assert result["stats"]["completed"] == 2

    def test_with_none_jobs_types_delegates(self, monkeypatch):
        mock_return = {"stats": {"total": 0}, "recent_jobs": []}
        mock_func = MagicMock(return_value=mock_return)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.get_all_user_jobs_stats", mock_func)
        result = get_user_jobs_stats("test_user", jobs_types=None)
        assert result == mock_return
        mock_func.assert_called_once_with("test_user", 100)

    def test_with_empty_jobs_types_delegates(self, monkeypatch):
        mock_return = {"stats": {"total": 5}, "recent_jobs": []}
        mock_func = MagicMock(return_value=mock_return)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.get_all_user_jobs_stats", mock_func)
        result = get_user_jobs_stats("test_user", jobs_types=[])
        assert result == mock_return
        mock_func.assert_called_once_with("test_user", 100)


# ── Active job checks ──


class TestHasActiveJob:
    """Tests for has_active_job."""

    def test_returns_true_when_active_job_exists(self):
        create_job("test_job", username="test_user")
        assert has_active_job("test_job") is True

    def test_returns_false_when_no_active_job(self):
        job = create_job("test_job", username="test_user")
        update_job_status(job.id, "completed", job_type="test_job")
        assert has_active_job("test_job") is False


# ── Cancellation ──


class TestCancelJobDb:
    """Tests for cancel_job_db."""

    def test_cancels_pending_job(self):
        job = create_job("test_job", username="test_user")
        result = cancel_job_db(job.id)
        assert result is True
        cancelled = get_job(job.id, "test_job")
        assert cancelled.status == "cancelled"

    def test_cancels_running_job(self):
        job = create_job("test_job", username="test_user")
        update_job_status(job.id, "running", job_type="test_job")
        result = cancel_job_db(job.id)
        assert result is True
        cancelled = get_job(job.id, "test_job")
        assert cancelled.status == "cancelled"

    def test_returns_false_when_not_pending_or_running(self):
        job = create_job("test_job", username="test_user")
        update_job_status(job.id, "completed", job_type="test_job")
        result = cancel_job_db(job.id)
        assert result is False

    def test_with_job_type_filter_works(self):
        job1 = create_job("type_a", username="test_user")
        create_job("type_b", username="test_user")
        result = cancel_job_db(job1.id, job_type="type_a")
        assert result is True
        cancelled = get_job(job1.id, "type_a")
        assert cancelled.status == "cancelled"


# ── Status updates ──


class TestUpdateJobStatus:
    """Tests for update_job_status."""

    def test_sets_started_at_when_running_and_not_previously_set(self):
        job = create_job("test_job", username="test_user")
        assert job.started_at is None
        updated = update_job_status(job.id, "running", job_type="test_job")
        assert updated.status == "running"
        assert updated.started_at is not None

    def test_sets_completed_at_for_final_statuses(self):
        job = create_job("test_job", username="test_user")
        updated = update_job_status(job.id, "completed", job_type="test_job")
        assert updated.status == "completed"
        assert updated.completed_at is not None

    def test_sets_completed_at_for_cancelled(self):
        job = create_job("test_job", username="test_user")
        updated = update_job_status(job.id, "cancelled", job_type="test_job")
        assert updated.status == "cancelled"
        assert updated.completed_at is not None

    def test_retries_on_connection_error(self, monkeypatch):
        mock_job = MagicMock()
        mock_job.started_at = None
        mock_job.status = "pending"
        mock_job.completed_at = None
        mock_job.result_file = None
        mock_job.is_running = 1

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.first.return_value = mock_job

        commit_call_count = [0]

        def mock_commit():
            commit_call_count[0] += 1
            if commit_call_count[0] == 1:
                error = OperationalError("stmt", {}, None)
                error.connection_invalidated = True
                raise error

        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.commit", mock_commit)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.refresh", lambda x: None)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.rollback", lambda: None)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.remove", lambda: None)

        result = update_job_status(1, "completed", job_type="test_job")
        assert result == mock_job
        assert result.status == "completed"
        assert commit_call_count[0] == 2

    def test_re_raises_after_max_retries(self, monkeypatch):
        mock_job = MagicMock()
        mock_job.started_at = None
        mock_job.status = "pending"
        mock_job.completed_at = None
        mock_job.result_file = None
        mock_job.is_running = 1

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.first.return_value = mock_job

        def mock_commit():
            error = OperationalError("stmt", {}, None)
            error.connection_invalidated = True
            raise error

        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.commit", mock_commit)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.refresh", lambda x: None)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.rollback", lambda: None)
        monkeypatch.setattr("src.main_app.db.services.jobs_service.db.session.remove", lambda: None)

        with pytest.raises(OperationalError):
            update_job_status(1, "completed", job_type="test_job")
