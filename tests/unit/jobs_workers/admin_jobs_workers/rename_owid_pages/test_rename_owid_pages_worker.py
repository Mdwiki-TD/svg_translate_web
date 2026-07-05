"""Unit tests for rename_owid_pages/worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.worker import (
    MOVE_REASON,
    PREFIXES,
    RenameInfo,
    RenameOwidPagesWorker,
    needs_rename,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_worker_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.worker.RenameOwidPagesWorker",
        _mock_class,
    )
    return _mock_class


@pytest.fixture
def mock_db_services(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Mock get_template_by_title and update_template_data."""
    mocks = {
        "get_template_by_title": MagicMock(return_value=None),
        "update_template_data": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.worker.get_template_by_title",
        mocks["get_template_by_title"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.worker.update_template_data",
        mocks["update_template_data"],
    )
    return mocks


def _make_mwclient_page_mock(*, exists: bool = True, is_redirect: bool = False) -> MagicMock:
    """Create a mock MwClientPage with controlled exists() and is_redirect()."""
    mock_page = MagicMock(name="MwClientPage")
    mock_page.exists.return_value = exists
    mock_page.is_redirect.return_value = is_redirect
    mock_page.title = "Test_Page"
    return mock_page


def _make_worker(**kwargs) -> RenameOwidPagesWorker:
    """Create a RenameOwidPagesWorker with test-friendly defaults."""
    defaults = {"job_id": 1, "user": {"username": "tester"}, "cancel_event": None}
    defaults.update(kwargs)
    return RenameOwidPagesWorker(**defaults)


# ── tests: needs_rename ───────────────────────────────────────────────────────────


class TestNeedsRename:
    def test_lowercase_first_char_returns_true(self):
        yes, new_title = needs_rename("Template:OWID/daily_meat_consumption", "Template:OWID/")
        assert yes is True
        assert new_title == "Template:OWID/Daily_meat_consumption"

    def test_uppercase_first_char_returns_false(self):
        yes, new_title = needs_rename("Template:OWID/Daily_meat_consumption", "Template:OWID/")
        assert yes is False
        assert new_title == "Template:OWID/Daily_meat_consumption"

    def test_non_alpha_first_char_returns_false(self):
        yes, new_title = needs_rename("Template:OWID/123_data", "Template:OWID/")
        assert yes is False

    def test_title_not_starting_with_prefix_returns_false(self):
        yes, new_title = needs_rename("Template:Other/something", "Template:OWID/")
        assert yes is False
        assert new_title == "Template:Other/something"

    def test_empty_after_prefix_returns_false(self):
        yes, new_title = needs_rename("Template:OWID/", "Template:OWID/")
        assert yes is False
        assert new_title == "Template:OWID/"

    def test_main_namespace_prefix(self):
        yes, new_title = needs_rename("OWID/some_page", "OWID/")
        assert yes is True
        assert new_title == "OWID/Some_page"

    def test_preserves_underscores_and_spaces(self):
        yes, new_title = needs_rename("Template:OWID/snake_case_name", "Template:OWID/")
        assert yes is True
        assert new_title == "Template:OWID/Snake_case_name"


# ── tests: RenameInfo ─────────────────────────────────────────────────────────


class TestRenameInfo:
    def test_default_values(self):
        info = RenameInfo(namespace=0, old_title="Old")
        assert info.namespace == 0
        assert info.old_title == "Old"
        assert info.new_title is None
        assert info.status == "pending"
        assert info.msg == ""
        assert info.newrevid is None
        assert info.timestamp

    def test_to_dict(self):
        info = RenameInfo(namespace=10, old_title="Old", new_title="New", status="renamed", msg="ok")
        d = info.to_dict()
        assert d["namespace"] == 10
        assert d["old_title"] == "Old"
        assert d["new_title"] == "New"
        assert d["status"] == "renamed"
        assert d["msg"] == "ok"
        assert "timestamp" in d


# ── tests: RenameOwidPagesWorker.__init__ ─────────────────────────────────────


class TestWorkerInit:
    def test_default_initialization(self, mock_base_worker):
        _worker = _make_worker()
        assert _worker.job_id == 1
        assert _worker.user == {"username": "tester"}
        assert _worker.cancel_event is None
        assert _worker.args == {}
        assert _worker.site is None

    def test_args_passed(self, mock_base_worker):
        _worker = _make_worker(args={"some": "value"})
        assert _worker.args == {"some": "value"}

    def test_get_job_type(self, mock_base_worker):
        _worker = _make_worker()
        assert _worker.get_job_type() == "rename_owid_pages"

    def test_initial_result_structure(self, mock_base_worker):
        _worker = _make_worker()
        result = _worker.result
        assert result.status == "pending"
        assert result.summary.total == 0
        assert result.summary.processed == 0
        assert result.summary.renamed == 0
        assert result.summary.skipped_target_exists == 0
        assert result.summary.redirected == 0
        assert result.summary.failed == 0
        assert result.pages_processed == []
        assert result.started_at is not None


# ── tests: process() ──────────────────────────────────────────────────────────


class TestProcess:
    def test_no_site_authentication(self, mock_base_worker):
        mock_base_worker["get_user_site"].return_value = None

        _worker = _make_worker()
        result = _worker.process()
        assert result.status == "failed"


# ── tests: _rename_one ────────────────────────────────────────────────────────


class TestRenameOne:
    """Tests for _rename_one covering all branches of the target-exists logic."""

    # ── helpers ─────────────────────────────────────────────────────────

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, mock_base_worker, mock_db_services):
        """Create a worker and patch MwClientPage."""
        _worker = _make_worker()

        self._mock_page_cls = MagicMock(name="MwClientPage_class")
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.worker.MwClientPage",
            self._mock_page_cls,
        )
        monkeypatch.setattr(_worker, "_update_template_title", MagicMock())
        self.worker = _worker

    def _set_pages(self, new_exists, new_is_redirect, old_is_redirect):
        """Configure the mock MwClientPage instances returned by the class.

        Stores the mock pages as self._mock_new_page / self._mock_old_page so
        individual tests can configure .move() / .edit() on them.
        """
        self._mock_new_page = _make_mwclient_page_mock(exists=new_exists, is_redirect=new_is_redirect)
        self._mock_new_page.title = "Template:OWID/Daily"
        self._mock_old_page = _make_mwclient_page_mock(exists=True, is_redirect=old_is_redirect)
        self._mock_old_page.title = "Template:OWID/daily"
        self._mock_page_cls.side_effect = [self._mock_new_page, self._mock_old_page]

    # ── branch: new_title does NOT exist → move ──────────────────────────

    def test_move_success(self):

        self._set_pages(new_exists=False, new_is_redirect=False, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": True, "newrevid": 42}

        result = self.worker._rename_one(10, "Template:OWID/daily", "Template:OWID/Daily")

        assert result is True
        assert self.worker.result.summary.renamed == 1
        assert self.worker.result.summary.failed == 0

    def test_move_failure(self):

        self._set_pages(new_exists=False, new_is_redirect=False, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": False, "error": "permission denied"}

        result = self.worker._rename_one(10, "Template:OWID/daily", "Template:OWID/Daily")

        assert result is False
        assert self.worker.result.summary.failed == 1

    def test_move_failure_with_details(self, mock_base_worker, mock_db_services):

        self._set_pages(new_exists=False, new_is_redirect=False, old_is_redirect=False)

        self._mock_old_page.move.return_value = {
            "success": False,
            "error": "blocked",
            "details": "Title blacklist",
        }

        result = self.worker._rename_one(10, "Template:OWID/daily", "Template:OWID/Daily")

        assert result is False
        assert self.worker.result.summary.failed == 1

    # ── branch: new_title exists, is redirect → overwrite via move ───────

    def test_target_is_redirect_overwrite_succeeds(self):

        self._set_pages(new_exists=True, new_is_redirect=True, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": True, "newrevid": 99}

        result = self.worker._rename_one(10, "Template:OWID/daily", "Template:OWID/Daily")

        assert result is True
        assert self.worker.result.summary.renamed == 1

    def test_target_is_redirect_overwrite_fails(self):

        self._set_pages(new_exists=True, new_is_redirect=True, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": False, "error": "error"}

        result = self.worker._rename_one(10, "Template:OWID/daily", "Template:OWID/Daily")

        assert result is False
        assert self.worker.result.summary.failed == 1

    # ── branch: new_title exists, old is redirect → skip + DB update ─────

    def test_source_is_redirect_skip_and_update_db(self):

        self._set_pages(new_exists=True, new_is_redirect=False, old_is_redirect=True)

        result = self.worker._rename_one(10, "Template:OWID/daily", "Template:OWID/Daily")

        assert result is False
        assert self.worker.result.summary.skipped_target_exists == 1
        assert self.worker.result.summary.failed == 0
        self.worker._update_template_title.assert_called_once_with("Template:OWID/daily", "Template:OWID/Daily")  # type: ignore

    # ── branch: new_title exists, neither is redirect → redirect old ─────

    def test_both_real_pages_redirects_old_to_new(self, monkeypatch):

        self._set_pages(new_exists=True, new_is_redirect=False, old_is_redirect=False)

        # Mock _redirect_old_to_new
        with monkeypatch.context() as m:
            mock_redirect = MagicMock(return_value=True)
            m.setattr(self.worker, "_redirect_old_to_new", mock_redirect)

            result = self.worker._rename_one(10, "Template:OWID/daily", "Template:OWID/Daily")

            mock_redirect.assert_called_once()
            call_args = mock_redirect.call_args
            # First arg is info (RenameInfo), second is old_title_page (MwClientPage), third is new_title (str)
            assert call_args[0][2] == "Template:OWID/Daily"

        assert result is True


# ── tests: _redirect_old_to_new ───────────────────────────────────────────────


class TestRedirectOldToNew:

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, mock_base_worker, mock_db_services):
        self.worker = _make_worker()
        monkeypatch.setattr(self.worker, "_update_template_title", MagicMock())

    def test_redirect_success(self):

        info = RenameInfo(namespace=10, old_title="Template:OWID/daily", new_title="Template:OWID/Daily")

        mock_page = MagicMock(name="old_title_page")
        mock_page.title = "Template:OWID/daily"
        mock_page.edit.return_value = {"success": True, "newrevid": 55}

        result = self.worker._redirect_old_to_new(info, mock_page, "Template:OWID/Daily")

        assert result is True
        assert info.status == "redirected"
        assert self.worker.result.summary.redirected == 1
        assert self.worker.result.summary.failed == 0
        mock_page.edit.assert_called_once_with(
            text="#REDIRECT [[Template:OWID/Daily]]",
            summary="Redirecting to [[Template:OWID/Daily]] (capitalize first letter of OWID subpage)",
        )

    def test_redirect_failure(self):
        info = RenameInfo(namespace=10, old_title="Template:OWID/daily", new_title="Template:OWID/Daily")

        mock_page = MagicMock(name="old_title_page")
        mock_page.title = "Template:OWID/daily"
        mock_page.edit.return_value = {"success": False, "error": "protected page"}

        result = self.worker._redirect_old_to_new(info, mock_page, "Template:OWID/Daily")

        assert result is False
        assert info.status == "failed"
        assert self.worker.result.summary.failed == 1

    def test_redirect_failure_with_details(self):
        info = RenameInfo(namespace=10, old_title="Template:OWID/daily", new_title="Template:OWID/Daily")

        mock_page = MagicMock(name="old_title_page")
        mock_page.title = "Template:OWID/daily"
        mock_page.edit.return_value = {"success": False, "error": "blocked", "details": "abuse filter"}

        result = self.worker._redirect_old_to_new(info, mock_page, "Template:OWID/Daily")

        assert result is False
        assert info.status == "failed"


# ── tests: _update_template_title ─────────────────────────────────────────────


class TestUpdateTemplateTitle:
    def test_updates_title_when_record_found(self, mock_base_worker, mock_db_services):
        _worker = _make_worker()
        mock_record = MagicMock()
        mock_record.id = 7
        mock_db_services["get_template_by_title"].return_value = mock_record

        _worker._update_template_title("Old", "New")

        mock_db_services["get_template_by_title"].assert_called_once_with("Old")
        mock_db_services["update_template_data"].assert_called_once_with(7, {"title": "New"})

    def test_noop_when_record_not_found(self, mock_base_worker, mock_db_services):
        _worker = _make_worker()
        mock_db_services["get_template_by_title"].return_value = None

        _worker._update_template_title("Old", "New")

        mock_db_services["update_template_data"].assert_not_called()

    def test_handles_exception_gracefully(self, mock_base_worker, mock_db_services):
        _worker = _make_worker()
        mock_db_services["get_template_by_title"].side_effect = RuntimeError("DB down")

        _worker._update_template_title("Old", "New")

        mock_db_services["update_template_data"].assert_not_called()

# ── Edge Cases ─────────────────────────────────────────────────────────────────


class TestWorkerEdgeCases:
    def test_cancel_event_set_stops_processing(self, mock_base_worker, mock_db_services):
        cancel_event = threading.Event()
        cancel_event.set()
        _worker = _make_worker(cancel_event=cancel_event)
        _worker.process()
        assert _worker.result.status == "cancelled"

    def test_module_constants(self):
        assert MOVE_REASON == "Capitalize first letter of OWID subpage name"
        assert len(PREFIXES) == 2
        assert (10, "OWID/", "Template:OWID/") in PREFIXES
        assert (0, "OWID/", "OWID/") in PREFIXES
