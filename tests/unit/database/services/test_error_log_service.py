# ruff: noqa: F401
"""
Unit tests for src/main_app/database/services/error_log_service.py module.

Classes to test: ErrorLogService
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from src.main_app.database import db
from src.main_app.database.models.error_log_models import ErrorLogDaily, ErrorLogRecord
from src.main_app.database.services.error_log_service import ErrorLogService, _cut, _path_hash, _utcnow


# ---------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------
class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = ErrorLogService()

    def _make_log(
        self,
        status_code: int = 404,
        path: str = "/test",
        ip: str = "127.0.0.1",
        suspected_bot: bool = False,
        created_at: datetime | None = None,
    ) -> ErrorLogRecord:
        """Insert an error log row directly."""
        record = ErrorLogRecord(
            status_code=status_code,
            method="GET",
            path=path,
            ip=ip,
            suspected_bot=suspected_bot,
        )
        if created_at is not None:
            record.created_at = created_at
        db.session.add(record)
        db.session.commit()
        return record

    def _make_daily(
        self,
        status_code: int = 404,
        path: str = "/test",
        hits: int = 1,
        bot_hits: int = 0,
        day: date | None = None,
        last_seen: datetime | None = None,
    ) -> ErrorLogDaily:
        """Insert an error_log_daily counter row directly."""
        now = _utcnow()
        record = ErrorLogDaily(
            day=day or now.date(),
            status_code=status_code,
            path=path,
            path_hash=_path_hash(path),
            hits=hits,
            bot_hits=bot_hits,
            last_seen=last_seen or now,
        )
        db.session.add(record)
        db.session.commit()
        return record


# ---------------------------------------------------------------
# 1. Tests for _cut helper
# ---------------------------------------------------------------
class TestCutHelper:
    """Tests for the _cut utility function."""

    def test_truncates_long_value(self):
        assert _cut("abcdefghij", 5) == "abcde"

    def test_returns_none_for_none(self):
        assert _cut(None, 10) is None

    def test_returns_full_string_when_short(self):
        assert _cut("hi", 100) == "hi"

    def test_converts_non_string_to_str(self):
        assert _cut(42, 10) == "42"


# ---------------------------------------------------------------
# 2. Tests for top_paths
# ---------------------------------------------------------------
class TestTopPaths(TestSetup):
    """Tests for the top_paths method (reads from error_log_daily)."""

    def test_returns_empty_when_no_logs(self):
        assert self.service.top_paths() == []

    def test_returns_most_hit_paths(self):
        self._make_daily(path="/a", status_code=404, hits=2)
        self._make_daily(path="/b", status_code=500, hits=1)

        result = self.service.top_paths()
        assert len(result) >= 1
        assert result[0]["path"] == "/a"
        assert result[0]["hits"] == 2

    def test_respects_limit(self):
        for i in range(5):
            self._make_daily(path=f"/p{i}")
        result = self.service.top_paths(limit=2)
        assert len(result) == 2

    def test_includes_bot_hits_count(self):
        self._make_daily(path="/bot", hits=2, bot_hits=1)
        result = self.service.top_paths()
        assert result[0]["bot_hits"] == 1


# ---------------------------------------------------------------
# 3. Tests for status_summary
# ---------------------------------------------------------------
class TestStatusSummary(TestSetup):
    """Tests for the status_summary method (reads from error_log_daily)."""

    def test_returns_empty_when_no_logs(self):
        assert self.service.status_summary() == []

    def test_groups_by_status_code(self):
        self._make_daily(status_code=404, hits=2)
        self._make_daily(status_code=500, hits=1)

        result = self.service.status_summary()
        codes = {r["status_code"]: r["hits"] for r in result}
        assert codes[404] == 2
        assert codes[500] == 1

    def test_includes_bot_hits(self):
        self._make_daily(status_code=404, hits=2, bot_hits=2)

        result = self.service.status_summary()
        entry = next(r for r in result if r["status_code"] == 404)
        assert entry["bot_hits"] == 2


# ---------------------------------------------------------------
# 4. Tests for search
# ---------------------------------------------------------------
class TestSearch(TestSetup):
    """Tests for the search method."""

    def test_returns_all_recent_logs(self):
        self._make_log(path="/x")
        self._make_log(path="/y")
        result = self.service.search()
        assert result.total >= 2

    def test_filters_by_status_code(self):
        self._make_log(status_code=404)
        self._make_log(status_code=500)
        result = self.service.search(status_code=404)
        for item in result.items:
            assert item.status_code == 404

    def test_filters_by_path_substring(self):
        self._make_log(path="/api/data")
        self._make_log(path="/home")
        result = self.service.search(path="api")
        assert result.total >= 1
        assert all("api" in item.path for item in result.items)

    def test_filters_by_ip(self):
        self._make_log(ip="10.0.0.1")
        self._make_log(ip="10.0.0.2")
        result = self.service.search(ip="10.0.0.1")
        assert all(item.ip == "10.0.0.1" for item in result.items)

    def test_filters_by_suspected_bot(self):
        self._make_log(suspected_bot=True)
        self._make_log(suspected_bot=False)
        result = self.service.search(suspected_bot=True)
        assert all(item.suspected_bot for item in result.items)

    def test_pagination(self):
        for i in range(10):
            self._make_log(path=f"/page/{i}")
        result = self.service.search(page=1, per_page=3)
        assert len(result.items) == 3
        assert result.total == 10


# ---------------------------------------------------------------
# 5. Tests for purge_older_than
# ---------------------------------------------------------------
class TestPurgeOlderThan(TestSetup):
    """Tests for the purge_older_than method."""

    def test_deletes_old_rows(self):
        # purge_older_than refuses to run unless error_log_daily has rows
        self._make_daily()  # satisfy the guard
        old_date = datetime.now().replace(tzinfo=None) - timedelta(days=60)
        self._make_log(created_at=old_date)
        self._make_log()  # recent

        deleted = self.service.purge_older_than(days=30)
        assert deleted >= 1
        assert self.service.count() >= 1  # recent one survives

    def test_returns_zero_when_nothing_to_purge(self):
        self._make_log()  # recent
        deleted = self.service.purge_older_than(days=30)
        assert deleted == 0

    def test_keeps_rows_within_window(self):
        self._make_log()
        self.service.purge_older_than(days=30)
        assert self.service.count() == 1


# ---------------------------------------------------------------
# 6. Tests for log_request (mocks Flask request context)
# ---------------------------------------------------------------
class TestLogRequest(TestSetup):
    """Tests for the log_request method."""

    def test_log_request_writes_record(self, mock_app):
        """log_request should persist an error log row inside a request context."""
        with mock_app.test_request_context("/broken?q=1", method="GET"):
            self.service.log_request(500, "Internal Error", query="q=1", ip="1.2.3.4")

        # Verify a row was written
        assert self.service.count() >= 1
        record = self.service.list_all()[0]
        assert record.status_code == 500
        assert record.path == "/broken"
        assert record.ip == "1.2.3.4"

    def test_log_request_never_raises(self, mock_app):
        """log_request must not propagate exceptions."""
        with mock_app.test_request_context("/fail"):
            # Should not raise even if something goes wrong internally
            self.service.log_request(500, "Error")
