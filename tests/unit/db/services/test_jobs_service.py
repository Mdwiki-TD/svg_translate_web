"""Unit tests for jobs_service module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask import Flask
from sqlalchemy.exc import OperationalError

from src.main_app.db.exceptions import DuplicateRecordError
from src.main_app.db.models import JobRecord
from src.main_app.db.services.jobs_service import JobsService, _normalize_limit


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = JobsService()


class TestGet(TestSetup):
    def test_get_job(self):
        """Test retrieving a job by ID."""
        created_job = self.service.create_job("collect_templates_data", username="z")

        retrieved_job = self.service.get_job(created_job.id, job_type="collect_templates_data")

        assert retrieved_job.id == created_job.id
        assert retrieved_job.job_type == created_job.job_type

    def test_get_nonexistent_job(self):
        """Test retrieving a nonexistent job raises LookupError."""
        with pytest.raises(LookupError, match="Job id 999 was not found"):
            self.service.get_job(999, job_type="collect_templates_data")


class TestList(TestSetup):
    def test_list_jobs(self):
        """Test listing jobs."""
        job1 = self.service.create_job("collect_templates_data", username="z")
        self.service.update_job_status(job1.id, "completed", job_type="collect_templates_data")
        self.service.create_job("collect_templates_data", username="z")
        self.service.create_job("other_job", username="z")

        jobs = self.service.list_jobs()

        assert len(jobs) == 3
        assert all(isinstance(job, JobRecord) for job in jobs)

    def test_list_jobs_with_limit(self):
        """Test listing jobs with a limit."""
        for i in range(5):
            job = self.service.create_job("collect_templates_data", username="z")
            if i < 4:
                self.service.update_job_status(job.id, "completed", job_type="collect_templates_data")

        jobs = self.service.list_jobs(limit=2)

        assert len(jobs) == 2

    def test_list_jobs_filtered_by_type(self):
        """Test listing jobs filtered by job_type."""
        job1 = self.service.create_job("collect_templates_data", username="z")
        self.service.update_job_status(job1.id, "completed", job_type="collect_templates_data")
        self.service.create_job("collect_templates_data", username="z")
        self.service.create_job("fix_nested_main_files", username="z")
        self.service.create_job("other_job_type", username="z")

        collect_jobs = self.service.list_jobs(job_type="collect_templates_data")
        assert len(collect_jobs) == 2
        assert all(job.job_type == "collect_templates_data" for job in collect_jobs)

        fix_jobs = self.service.list_jobs(job_type="fix_nested_main_files")
        assert len(fix_jobs) == 1
        assert all(job.job_type == "fix_nested_main_files" for job in fix_jobs)

        all_jobs = self.service.list_jobs()
        assert len(all_jobs) == 4

    def test_list_jobs_filtered_with_limit(self):
        """Test listing jobs filtered by job_type with a limit."""
        for i in range(5):
            job = self.service.create_job("collect_templates_data", username="z")
            if i < 4:
                self.service.update_job_status(job.id, "completed", job_type="collect_templates_data")
        for i in range(3):
            job = self.service.create_job("fix_nested_main_files", username="z")
            if i < 2:
                self.service.update_job_status(job.id, "completed", job_type="fix_nested_main_files")

        collect_jobs = self.service.list_jobs(limit=2, job_type="collect_templates_data")
        assert len(collect_jobs) == 2
        assert all(job.job_type == "collect_templates_data" for job in collect_jobs)


class TestDelete(TestSetup):
    def test_delete_job(self):
        """Test deleting a job."""
        job = self.service.create_job("collect_templates_data", username="z")
        assert len(self.service.list_jobs()) == 1

        self.service.delete_job_by_id_and_type(job.id, "collect_templates_data")
        jobs_len = len(self.service.list_jobs())
        assert jobs_len == 0

    def test_delete_job_with_correct_type(self):
        """Test deleting a job with correct job type."""
        job1 = self.service.create_job("collect_templates_data", username="z")
        job2 = self.service.create_job("fix_nested_main_files", username="z")
        assert len(self.service.list_jobs()) == 2

        self.service.delete_job_by_id_and_type(job1.id, "collect_templates_data")

        remaining_jobs = self.service.list_jobs()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == job2.id

    def test_delete_job_with_wrong_type(self):
        """Test deleting a job with wrong job type doesn't delete it."""
        job = self.service.create_job("collect_templates_data", username="z")
        assert len(self.service.list_jobs()) == 1

        self.service.delete_job_by_id_and_type(job.id, "fix_nested_main_files")

        remaining_jobs = self.service.list_jobs()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == job.id

    def test_delete_nonexistent_job(self):
        """Test deleting a non-existent job."""
        self.service.delete_job_by_id_and_type(999, "collect_templates_data")

        assert len(self.service.list_jobs()) == 0

    def test_update_job_status_nonexistent(self):
        """Test updating status of a nonexistent job raises LookupError."""
        with pytest.raises(LookupError):
            self.service.update_job_status(999, "completed", job_type="test_job")


class TestNormalizeLimit(TestSetup):
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


class TestIsJobCancelled(TestSetup):
    """Tests for is_job_cancelled."""

    def test_cancelled_status_returns_true(self):
        mock_record = MagicMock()
        mock_record.status = "cancelled"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        self.service.session.query = mock_query

        result = self.service.is_job_cancelled(1, "test")
        assert result is True

    def test_active_statuses_return_false(self):
        for status in ("pending", "running", "completed"):
            mock_record = MagicMock()
            mock_record.status = status
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = mock_record

            self.service.session.query = mock_query

            result = self.service.is_job_cancelled(1, "test")
            assert result is False

    def test_no_record_returns_false(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.service.session.query = mock_query
        result = self.service.is_job_cancelled(1, "test")
        assert result is False

    def test_refresh_called_before_checking_status(self):
        mock_record = MagicMock()
        mock_record.status = "cancelled"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        refresh = MagicMock()
        self.service.session.query = mock_query
        self.service.session.refresh = refresh
        self.service.is_job_cancelled(1, "test")
        refresh.assert_called_once_with(mock_record)


class TestGetJob(TestSetup):
    """Tests for get_job."""

    def test_returns_job_when_found(self):
        job = self.service.create_job("test_job", username="test_user")
        result = self.service.get_job(job.id, "test_job")
        assert result.id == job.id
        assert result.job_type == "test_job"

    def test_raises_lookup_error_when_not_found(self):
        with pytest.raises(LookupError, match="Job id 999 was not found"):
            self.service.get_job(999, "test_job")


class TestListJobs(TestSetup):
    """Tests for list_jobs."""

    def test_empty_list_when_no_jobs(self):
        jobs = self.service.list_jobs()
        assert jobs == []


class TestGetAllUserJobsStats(TestSetup):
    """Tests for get_all_user_jobs_stats."""

    def test_returns_stats_with_correct_counts(self):
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

        self.service.session.query = query_side_effect

        result = self.service.get_all_user_jobs_stats("test_user")
        assert result["stats"]["total"] == 7  # type: ignore
        assert result["stats"]["completed"] == 5  # type: ignore
        assert result["stats"]["failed"] == 2  # type: ignore

    def test_handles_empty_records(self):
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

        self.service.session.query = query_side_effect

        result = self.service.get_all_user_jobs_stats("test_user")
        assert result["stats"]["total"] == 0  # type: ignore
        assert result["stats"]["completed"] == 0  # type: ignore
        assert result["stats"]["failed"] == 0  # type: ignore
        assert result["recent_jobs"] == []

    def test_respects_limit_parameter(self):
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

        self.service.session.query = query_side_effect

        result = self.service.get_all_user_jobs_stats("test_user", limit=5)
        assert result["stats"]["total"] == 3  # type: ignore
        assert result["stats"]["completed"] == 3  # type: ignore
        assert len(result["recent_jobs"]) == 1


class TestGetUserJobsStats(TestSetup):
    """Tests for get_user_jobs_stats."""

    def test_with_jobs_types_filters_correctly(self):
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

        self.service.session.query = query_side_effect

        result = self.service.get_user_jobs_stats("test_user", jobs_types=["type_a", "type_b"])
        assert result["stats"]["total"] == 2  # type: ignore
        assert result["stats"]["completed"] == 2  # type: ignore

    def test_with_none_jobs_types_delegates(self):
        mock_return = {"stats": {"total": 0}, "recent_jobs": []}
        mock_method = MagicMock(return_value=mock_return)

        self.service._get_all_user_jobs_stats = mock_method
        result = self.service.get_user_jobs_stats("test_user", jobs_types=None)
        assert result == mock_return
        mock_method.assert_called_once_with("test_user", 100)

    def test_with_empty_jobs_types_delegates(self):
        mock_return = {"stats": {"total": 5}, "recent_jobs": []}
        mock_method = MagicMock(return_value=mock_return)

        self.service._get_all_user_jobs_stats = mock_method
        result = self.service.get_user_jobs_stats("test_user", jobs_types=[])
        assert result == mock_return
        mock_method.assert_called_once_with("test_user", 100)


class TestHasActiveJob(TestSetup):
    """Tests for has_active_job."""

    def test_returns_true_when_active_job_exists(self):
        self.service.create_job("test_job", username="test_user")
        assert self.service.has_active_job("test_job") is True

    def test_returns_false_when_no_active_job(self):
        job = self.service.create_job("test_job", username="test_user")
        self.service.update_job_status(job.id, "completed", job_type="test_job")
        assert self.service.has_active_job("test_job") is False


class TestCancelJobDb(TestSetup):
    """Tests for cancel_job_db."""

    def test_cancels_pending_job(self):
        job = self.service.create_job("test_job", username="test_user")
        result = self.service.cancel_job_db(job.id)
        assert result is True
        cancelled = self.service.get_job(job.id, "test_job")
        assert cancelled.status == "cancelled"

    def test_cancels_running_job(self):
        job = self.service.create_job("test_job", username="test_user")
        self.service.update_job_status(job.id, "running", job_type="test_job")
        result = self.service.cancel_job_db(job.id)
        assert result is True
        cancelled = self.service.get_job(job.id, "test_job")
        assert cancelled.status == "cancelled"

    def test_returns_false_when_not_pending_or_running(self):
        job = self.service.create_job("test_job", username="test_user")
        self.service.update_job_status(job.id, "completed", job_type="test_job")
        result = self.service.cancel_job_db(job.id)
        assert result is False

    def test_with_job_type_filter_works(self):
        job1 = self.service.create_job("type_a", username="test_user")
        self.service.create_job("type_b", username="test_user")
        result = self.service.cancel_job_db(job1.id, job_type="type_a")
        assert result is True
        cancelled = self.service.get_job(job1.id, "type_a")
        assert cancelled.status == "cancelled"


class TestUpdateJobStatus(TestSetup):
    """Tests for update_job_status."""

    def test_sets_started_at_when_running_and_not_previously_set(self):
        job = self.service.create_job("test_job", username="test_user")
        assert job.started_at is None
        updated = self.service.update_job_status(job.id, "running", job_type="test_job")
        assert updated.status == "running"
        assert updated.started_at is not None

    def test_sets_completed_at_for_final_statuses(self):
        job = self.service.create_job("test_job", username="test_user")
        updated = self.service.update_job_status(job.id, "completed", job_type="test_job")
        assert updated.status == "completed"
        assert updated.completed_at is not None

    def test_sets_completed_at_for_cancelled(self):
        job = self.service.create_job("test_job", username="test_user")
        updated = self.service.update_job_status(job.id, "cancelled", job_type="test_job")
        assert updated.status == "cancelled"
        assert updated.completed_at is not None

    def test_re_raises_after_max_retries(self):
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

        self.service.session.query = mock_query
        self.service.session.commit = mock_commit

        self.service.session.rollback = MagicMock()
        self.service.session.remove = MagicMock()

        with pytest.raises(OperationalError):
            self.service.update_job_status(1, "completed", job_type="test_job")

    def test_update_job_status(self):
        """Test updating a job's status."""
        job = self.service.create_job("collect_templates_data", username="z")

        updated_job = self.service.update_job_status(job.id, "running", job_type="collect_templates_data")

        assert updated_job.status == "running"

    def test_update_job_status_with_result_file(self):
        """Test updating a job's status with a result file."""
        job = self.service.create_job("collect_templates_data", username="z")

        updated_job = self.service.update_job_status(
            job.id, "completed", "/path/to/result.json", job_type="collect_templates_data"
        )

        assert updated_job.status == "completed"
        assert updated_job.result_file == "/path/to/result.json"


class TestUpdateJobStatusWithRetry(TestSetup):
    """Tests for update_job_status_with_retry."""

    def test_retries_on_connection_error(self):
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

        self.service.session.query = mock_query
        self.service.session.commit = mock_commit

        self.service.session.rollback = MagicMock()
        self.service.session.remove = MagicMock()

        result = self.service.update_job_status_with_retry(1, "completed", job_type="test_job")
        assert result == mock_job
        assert result.status == "completed"
        assert commit_call_count[0] == 2


class TestDeleteJob(TestSetup):
    def test_delete_existing_job(self, mock_app, setup_db):

        with mock_app.app_context():
            record = JobRecord(job_type="copy_svg_langs", status="completed", username="admin")
            self.service.session.add(record)
            self.service.session.commit()
            job_id = record.id

            result = self.service.delete_job_by_id_and_type(job_id, "copy_svg_langs")
            assert result is True
            self.service.session.expire_all()
            assert self.service.session.get(JobRecord, job_id) is None

    def test_delete_non_existent_job(self, mock_app, setup_db):
        with mock_app.app_context():
            result = self.service.delete_job_by_id_and_type(99999, "copy_svg_langs")
            assert result is False

    def test_delete_job_wrong_type(self, mock_app, setup_db):

        with mock_app.app_context():
            record = JobRecord(job_type="copy_svg_langs", status="completed", username="admin")
            self.service.session.add(record)
            self.service.session.commit()
            job_id = record.id

            result = self.service.delete_job_by_id_and_type(job_id, "wrong_type")
            assert result is False
            self.service.session.expire_all()
            assert self.service.session.get(JobRecord, job_id) is not None


class TestCreateJob(TestSetup):
    def test_create_duplicate_pending_job_raises_error(self, mock_app: Flask) -> None:
        """Creating a second pending job of the same type should raise DuplicateRecordError."""
        with mock_app.app_context():
            self.service.create_job(job_type="dup_pending_type", username="user1")
            with pytest.raises(DuplicateRecordError):
                self.service.create_job(job_type="dup_pending_type", username="user2")

    def test_create_duplicate_running_job_raises_error(self, mock_app: Flask) -> None:
        """Creating a job while one of same type is running should raise DuplicateRecordError."""
        with mock_app.app_context():
            job = self.service.create_job(job_type="dup_running_type", username="user1")
            self.service.update_job_status(job.id, "running", job_type="dup_running_type")
            with pytest.raises(DuplicateRecordError):
                self.service.create_job(job_type="dup_running_type", username="user2")

    def test_create_job(self):
        """Test creating a new job."""
        job = self.service.create_job("collect_templates_data", username="test_user")

        assert job is not None
        assert job.id == 1
        assert job.job_type == "collect_templates_data"
        assert job.status == "pending"

    def test_create_job_with_username(self):
        """Test creating a new job with username."""
        job = self.service.create_job("collect_templates_data", username="test_user")

        assert job is not None
        assert job.id == 1
        assert job.job_type == "collect_templates_data"
        assert job.status == "pending"
        assert job.username == "test_user"
