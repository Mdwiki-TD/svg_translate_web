"""Unit tests for jobs_service module."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.exc import OperationalError

from src.main_app.database.exceptions import DuplicateRecordError
from src.main_app.database.models import JobRecord
from src.main_app.database.services import JobsService, JobStats, UserJobsStats
from src.main_app.database.services.jobs_service import _normalize_limit


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = JobsService()


class TestGet(TestSetup):
    def test_get_job(self) -> None:
        """Test retrieving a job by ID."""
        created_job = self.service.create_job("collect_templates_data", username="userx")

        retrieved_job = self.service.get_job(created_job.id, job_type="collect_templates_data")

        assert retrieved_job.id == created_job.id
        assert retrieved_job.job_type == created_job.job_type

    def test_get_nonexistent_job(self) -> None:
        """Test retrieving a nonexistent job raises LookupError."""
        with pytest.raises(LookupError, match="Job id 999 was not found"):
            self.service.get_job(999, job_type="collect_templates_data")


class TestList(TestSetup):
    def test_list_jobs(self) -> None:
        """Test listing jobs."""
        job1 = self.service.create_job("collect_templates_data", username="userx")
        self.service.update_job_status(job1.id, "completed", job_type="collect_templates_data")
        self.service.create_job("collect_templates_data", username="userx")
        self.service.create_job("other_job", username="userx")

        jobs = self.service.list_jobs()

        assert len(jobs) == 3
        assert all(isinstance(job, JobRecord) for job in jobs)

    def test_list_jobs_with_limit(self) -> None:
        """Test listing jobs with a limit."""
        for i in range(5):
            job = self.service.create_job("collect_templates_data", username="userx")
            if i < 4:
                self.service.update_job_status(job.id, "completed", job_type="collect_templates_data")

        jobs = self.service.list_jobs(limit=2)

        assert len(jobs) == 2

    def test_list_jobs_filtered_by_type(self) -> None:
        """Test listing jobs filtered by job_type."""
        job1 = self.service.create_job("collect_templates_data", username="userx")
        self.service.update_job_status(job1.id, "completed", job_type="collect_templates_data")
        self.service.create_job("collect_templates_data", username="userx")
        self.service.create_job("fix_nested_main_files", username="userx")
        self.service.create_job("other_job_type", username="userx")

        collect_jobs = self.service.list_jobs(job_type="collect_templates_data")
        assert len(collect_jobs) == 2
        assert all(job.job_type == "collect_templates_data" for job in collect_jobs)

        fix_jobs = self.service.list_jobs(job_type="fix_nested_main_files")
        assert len(fix_jobs) == 1
        assert all(job.job_type == "fix_nested_main_files" for job in fix_jobs)

        all_jobs = self.service.list_jobs()
        assert len(all_jobs) == 4

    def test_list_jobs_filtered_with_limit(self) -> None:
        """Test listing jobs filtered by job_type with a limit."""
        for i in range(5):
            job = self.service.create_job("collect_templates_data", username="userx")
            if i < 4:
                self.service.update_job_status(job.id, "completed", job_type="collect_templates_data")
        for i in range(3):
            job = self.service.create_job("fix_nested_main_files", username="userx")
            if i < 2:
                self.service.update_job_status(job.id, "completed", job_type="fix_nested_main_files")

        collect_jobs = self.service.list_jobs(limit=2, job_type="collect_templates_data")
        assert len(collect_jobs) == 2
        assert all(job.job_type == "collect_templates_data" for job in collect_jobs)


class TestDelete(TestSetup):
    def test_delete_job(self) -> None:
        """Test deleting a job."""
        job = self.service.create_job("collect_templates_data", username="userx")
        assert len(self.service.list_jobs()) == 1

        self.service.delete_job_by_id_and_type(job.id, "collect_templates_data")
        jobs_len = len(self.service.list_jobs())
        assert jobs_len == 0

    def test_delete_job_with_correct_type(self) -> None:
        """Test deleting a job with correct job type."""
        job1 = self.service.create_job("collect_templates_data", username="userx")
        job2 = self.service.create_job("fix_nested_main_files", username="userx")
        assert len(self.service.list_jobs()) == 2

        self.service.delete_job_by_id_and_type(job1.id, "collect_templates_data")

        remaining_jobs = self.service.list_jobs()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == job2.id

    def test_delete_job_with_wrong_type(self) -> None:
        """Test deleting a job with wrong job type doesn't delete it."""
        job = self.service.create_job("collect_templates_data", username="userx")
        assert len(self.service.list_jobs()) == 1

        self.service.delete_job_by_id_and_type(job.id, "fix_nested_main_files")

        remaining_jobs = self.service.list_jobs()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == job.id

    def test_delete_nonexistent_job(self) -> None:
        """Test deleting a non-existent job."""
        self.service.delete_job_by_id_and_type(999, "collect_templates_data")

        assert len(self.service.list_jobs()) == 0

    def test_update_job_status_nonexistent(self) -> None:
        """Test updating status of a nonexistent job raises LookupError."""
        with pytest.raises(LookupError):
            self.service.update_job_status(999, "completed", job_type="test_job")


class TestNormalizeLimit(TestSetup):
    """Tests for _normalize_limit helper."""

    def test_returns_default_when_none(self) -> None:
        assert _normalize_limit(None) == 100

    def test_returns_default_when_zero_or_negative(self) -> None:
        assert _normalize_limit(0) == 100
        assert _normalize_limit(-1) == 100
        assert _normalize_limit(-100) == 100

    def test_caps_at_max_limit(self) -> None:
        assert _normalize_limit(1000) == 500
        assert _normalize_limit(501) == 500

    def test_returns_limit_when_within_range(self) -> None:
        assert _normalize_limit(50) == 50
        assert _normalize_limit(100) == 100
        assert _normalize_limit(500) == 500


class TestIsJobCancelled(TestSetup):
    """Tests for is_job_cancelled."""

    def test_cancelled_status_returns_true(self) -> None:
        job = self.service.create_job("test", username="test_user")
        self.service.update_job_status(job.id, "cancelled", job_type="test")

        result = self.service.is_job_cancelled(job.id, "test")
        assert result is True

    def test_active_statuses_return_false(self) -> None:
        for status in ("pending", "running", "completed"):
            job = self.service.create_job(f"test_{status}", username="test_user")
            if status != "pending":
                self.service.update_job_status(job.id, status, job_type=f"test_{status}")

            result = self.service.is_job_cancelled(job.id, f"test_{status}")
            assert result is False

    def test_no_record_returns_false(self) -> None:
        result = self.service.is_job_cancelled(1, "test")
        assert result is False


class TestGetJob(TestSetup):
    """Tests for get_job."""

    def test_returns_job_when_found(self) -> None:
        job = self.service.create_job("test_job", username="test_user")
        result = self.service.get_job(job.id, "test_job")
        assert result.id == job.id
        assert result.job_type == "test_job"

    def test_raises_lookup_error_when_not_found(self) -> None:
        with pytest.raises(LookupError, match="Job id 999 was not found"):
            self.service.get_job(999, "test_job")


class TestListJobs(TestSetup):
    """Tests for list_jobs."""

    def test_empty_list_when_no_jobs(self) -> None:
        jobs = self.service.list_jobs()
        assert jobs == []


class TestGetAllUserJobsStats(TestSetup):
    """Tests for get_all_user_jobs_stats."""

    def test_returns_stats_with_correct_counts(self) -> None:
        completed = self.service.create_job("completed_type", username="test_user")
        self.service.update_job_status(completed.id, "completed", job_type="completed_type")
        failed = self.service.create_job("failed_type", username="test_user")
        self.service.update_job_status(failed.id, "failed", job_type="failed_type")

        result = self.service.get_all_user_jobs_stats("test_user")
        assert isinstance(result, UserJobsStats)
        assert isinstance(result.stats, JobStats)
        assert result.stats.total == 2
        assert result.stats.completed == 1
        assert result.stats.failed == 1
        assert result.stats.cancelled == 0

    def test_handles_empty_records(self) -> None:
        result = self.service.get_all_user_jobs_stats("test_user")
        assert result == UserJobsStats.empty()
        assert result.stats.total == 0
        assert result.stats.completed == 0
        assert result.stats.failed == 0
        assert result.stats.cancelled == 0
        assert result.recent_jobs == []

    def test_respects_limit_parameter(self) -> None:
        for i in range(3):
            job = self.service.create_job(f"completed_type_{i}", username="test_user")
            self.service.update_job_status(job.id, "completed", job_type=f"completed_type_{i}")

        result = self.service.get_all_user_jobs_stats("test_user", limit=2)
        assert result.stats.total == 3
        assert result.stats.completed == 3
        assert len(result.recent_jobs) == 2


class TestGetUserJobsStats(TestSetup):
    """Tests for get_user_jobs_stats."""

    def test_with_jobs_types_filters_correctly(self) -> None:
        included = self.service.create_job("type_a", username="test_user")
        self.service.update_job_status(included.id, "completed", job_type="type_a")
        excluded = self.service.create_job("type_c", username="test_user")
        self.service.update_job_status(excluded.id, "failed", job_type="type_c")

        result = self.service.get_user_jobs_stats("test_user", jobs_types=["type_a", "type_b"])
        assert isinstance(result, UserJobsStats)
        assert result.stats.total == 1
        assert result.stats.completed == 1
        assert result.stats.failed == 0
        assert len(result.recent_jobs) == 1

    def test_with_none_jobs_types_delegates(self) -> None:
        job = self.service.create_job("type_a", username="test_user")
        self.service.update_job_status(job.id, "completed", job_type="type_a")

        result = self.service.get_user_jobs_stats("test_user", jobs_types=None)
        assert result.stats.total == 1
        assert result.stats.completed == 1

    def test_with_empty_jobs_types_delegates(self) -> None:
        job = self.service.create_job("type_a", username="test_user")
        self.service.update_job_status(job.id, "completed", job_type="type_a")

        result = self.service.get_user_jobs_stats("test_user", jobs_types=[])
        assert result.stats.total == 1
        assert result.stats.completed == 1


class TestHasActiveJob(TestSetup):
    """Tests for has_active_job."""

    def test_returns_true_when_active_job_exists(self) -> None:
        self.service.create_job("test_job", username="test_user")
        assert self.service.has_active_job("test_job") is True

    def test_returns_false_when_no_active_job(self) -> None:
        job = self.service.create_job("test_job", username="test_user")
        self.service.update_job_status(job.id, "completed", job_type="test_job")
        assert self.service.has_active_job("test_job") is False


class TestCancelJobDb(TestSetup):
    """Tests for cancel_job_db."""

    def test_cancels_pending_job(self) -> None:
        job = self.service.create_job("test_job", username="test_user")
        result = self.service.cancel_job_db(job.id)
        assert result is True
        cancelled = self.service.get_job(job.id, "test_job")
        assert cancelled.status == "cancelled"

    def test_cancels_running_job(self) -> None:
        job = self.service.create_job("test_job", username="test_user")

        self.service.update_job_status(job.id, "running", job_type="test_job")
        result = self.service.cancel_job_db(job.id)

        assert result is True
        cancelled = self.service.get_job(job.id, "test_job")
        assert cancelled.status == "cancelled"

    def test_returns_false_when_not_pending_or_running(self) -> None:
        job = self.service.create_job("test_job", username="test_user")
        self.service.update_job_status(job.id, "completed", job_type="test_job")
        result = self.service.cancel_job_db(job.id)
        assert result is False

    def test_with_job_type_filter_works(self) -> None:
        job1 = self.service.create_job("type_a", username="test_user")
        self.service.create_job("type_b", username="test_user")
        result = self.service.cancel_job_db(job1.id, job_type="type_a")
        assert result is True
        cancelled = self.service.get_job(job1.id, "type_a")
        assert cancelled.status == "cancelled"

    def test_cancels_running_job_without_updating_completed_at(self) -> None:
        job = self.service.create_job("test_job", username="test_user")

        date = datetime.fromisoformat("2023-01-01 00:00:00")

        self.service.update_job_status(job.id, "running", job_type="test_job")
        record = self.service.update(job, started_at=date, completed_at=date)
        assert record is not None

        result = self.service.cancel_job_db(job.id)

        assert result is True
        cancelled = self.service.get_job(job.id, "test_job")

        assert cancelled.status == "cancelled"
        assert str(cancelled.completed_at) == str(date)


class TestUpdateJobStatus(TestSetup):
    """Tests for update_job_status."""

    def test_sets_started_at_when_running_and_not_previously_set(self) -> None:
        job = self.service.create_job("test_job", username="test_user")
        assert job.started_at is None
        updated = self.service.update_job_status(job.id, "running", job_type="test_job")
        assert updated.status == "running"
        assert updated.started_at is not None

    def test_sets_completed_at_for_final_statuses(self) -> None:
        job = self.service.create_job("test_job", username="test_user")
        updated = self.service.update_job_status(job.id, "completed", job_type="test_job")
        assert updated.status == "completed"
        assert updated.completed_at is not None

    def test_sets_completed_at_for_cancelled(self) -> None:
        job = self.service.create_job("test_job", username="test_user")
        updated = self.service.update_job_status(job.id, "cancelled", job_type="test_job")
        assert updated.status == "cancelled"
        assert updated.completed_at is not None

    def test_update_job_status(self) -> None:
        """Test updating a job's status."""
        job = self.service.create_job("collect_templates_data", username="userx")

        updated_job = self.service.update_job_status(job.id, "running", job_type="collect_templates_data")

        assert updated_job.status == "running"

    def test_update_job_status_with_result_file(self) -> None:
        """Test updating a job's status with a result file."""
        job = self.service.create_job("collect_templates_data", username="userx")

        updated_job = self.service.update_job_status(
            job.id, "completed", "/path/to/result.json", job_type="collect_templates_data"
        )

        assert updated_job.status == "completed"
        assert updated_job.result_file == "/path/to/result.json"


class TestDeleteJob(TestSetup):
    def test_delete_existing_job(self) -> None:
        record = self.service.create(job_type="copy_svg_langs", status="completed", username="admin")
        job_id = record.id

        result = self.service.delete_job_by_id_and_type(job_id, "copy_svg_langs")
        assert result is True
        self.service.expire_all()
        assert self.service.get(job_id) is None

    def test_delete_non_existent_job(self) -> None:
        result = self.service.delete_job_by_id_and_type(99999, "copy_svg_langs")
        assert result is False

    def test_delete_job_wrong_type(self) -> None:
        record = self.service.create(job_type="copy_svg_langs", status="completed", username="admin")
        job_id = record.id

        result = self.service.delete_job_by_id_and_type(job_id, "wrong_type")
        assert result is False
        self.service.expire_all()
        assert self.service.get(job_id) is not None


class TestCreateJob(TestSetup):
    def test_create_duplicate_pending_job_raises_error(self) -> None:
        """Creating a second pending job of the same type should raise DuplicateRecordError."""
        self.service.create_job(job_type="dup_pending_type", username="user1")
        with pytest.raises(DuplicateRecordError):
            self.service.create_job(job_type="dup_pending_type", username="user2")

    def test_create_duplicate_running_job_raises_error(self) -> None:
        """Creating a job while one of same type is running should raise DuplicateRecordError."""
        job = self.service.create_job(job_type="dup_running_type", username="user1")
        self.service.update_job_status(job.id, "running", job_type="dup_running_type")
        with pytest.raises(DuplicateRecordError):
            self.service.create_job(job_type="dup_running_type", username="user2")

    def test_create_job(self) -> None:
        """Test creating a new job."""
        job = self.service.create_job("collect_templates_data", username="test_user")

        assert job is not None
        assert job.id == 1
        assert job.job_type == "collect_templates_data"


class TestWithMocks(TestSetup):
    """Tests for update_job_status_with_retry and update_job_status."""

    def test_retries_on_connection_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        job = self.service.create_job("test_job", username="test_user")

        real_commit = self.service.session.commit
        commit_call_count = [0]

        def mock_commit() -> None:
            commit_call_count[0] += 1
            if commit_call_count[0] == 1:
                error = OperationalError("stmt", {}, None)
                error.connection_invalidated = True
                raise error
            real_commit()

        # Keep this mock: the retry path requires a synthetic connection-invalidated OperationalError.
        monkeypatch.setattr(self.service.session, "commit", mock_commit)

        result = self.service.update_job_status_with_retry(
            job.id, "completed", job_type="test_job", remove_session=False
        )
        assert result.id == job.id
        assert result.status == "completed"
        assert commit_call_count[0] == 2

    def test_re_raises_after_max_retries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        job = self.service.create_job("test_job", username="test_user")

        def mock_commit() -> None:
            error = OperationalError("stmt", {}, None)
            error.connection_invalidated = True
            raise error

        # Keep this mock: the retry path requires a synthetic connection-invalidated OperationalError.
        monkeypatch.setattr(self.service.session, "commit", mock_commit)

        with pytest.raises(OperationalError):
            self.service.update_job_status(job.id, "completed", job_type="test_job")
