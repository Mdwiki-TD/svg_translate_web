"""Unit tests for rename_owid_pages/worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest
from src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.objects import RenameInfo
from src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.worker import (
    MOVE_REASON,
    PREFIXES,
    RenameOwidPagesWorker,
)
from src.main_app.jobs_workers.objects import JobsRunner

# ── Fixtures ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_template_service():
    """Mock get_template_by_title and update_template_data."""
    mock_get_template_by_title = MagicMock(return_value=None)
    mock_update_template_data = MagicMock()

    template_service = MagicMock()
    template_service.get_template_by_title = mock_get_template_by_title
    template_service.update_template_data = mock_update_template_data

    return template_service


def _make_mwclient_page_mock(*, exists: bool = True, is_redirect: bool = False) -> MagicMock:
    """Create a mock MwClientPage with controlled exists() and is_redirect()."""
    mock_page = MagicMock(name="MwClientPage")
    mock_page.exists.return_value = exists
    mock_page.is_redirect.return_value = is_redirect
    mock_page.title = "Test_Page"
    return mock_page


@pytest.fixture
def mock_mw_client_cls():
    _mock = MagicMock(name="MwClientPage_class")
    _mock.return_value = MagicMock()
    _mock.load.return_value = _mock

    return _mock


@pytest.fixture
def mock_worker(
    mock_mw_client_cls,
    mock_template_service,
    mock_base_worker,
) -> RenameOwidPagesWorker:
    """Create a RenameOwidPagesWorker with test-friendly defaults."""
    defaults = {"job_id": 1, "user": {"username": "tester"}, "cancel_event": None}

    return RenameOwidPagesWorker(
        data=JobsRunner(**defaults),
        template_service=mock_template_service,
        mw_client_cls=mock_mw_client_cls,
    )


# ── tests: RenameOwidPagesWorker.__init__ ─────────────────────────────────────


class TestWorkerInit:
    def test_default_initialization(self, mock_worker: RenameOwidPagesWorker) -> None:
        _worker = mock_worker
        assert _worker.job_id == 1
        assert _worker.user == {"username": "tester"}
        assert _worker.cancel_event is None
        assert _worker.args == {}
        assert _worker._site is None

    def test_job_type(self, mock_worker: RenameOwidPagesWorker) -> None:
        assert mock_worker.JOB_TYPE == "rename_owid_pages"

    def test_initial_result_structure(self, mock_worker: RenameOwidPagesWorker) -> None:
        _worker = mock_worker
        result = _worker.result
        assert result.status == "pending"
        assert result.summary.total == 0
        assert result.summary.processed == 0
        assert len(result.pages_renamed) == 0
        assert len(result.pages_redirected) == 0
        assert len(result.pages_failed) == 0
        assert result.pages_processed == []
        assert result.started_at is not None


# ── tests: process() ──────────────────────────────────────────────────────────


class TestProcess:
    def test_no_site_authentication(self, mock_worker, mock_base_worker):
        mock_base_worker["get_user_site"].return_value = None

        _worker = mock_worker
        result = _worker.process()
        assert result.status == "failed"


# ── tests: _process_one_item ────────────────────────────────────────────────────────


class TestRenameOne:
    """Tests for _process_one_item covering all branches of the target-exists logic."""

    # ── helpers ─────────────────────────────────────────────────────────

    @pytest.fixture(autouse=True)
    def setup(self, mock_mw_client_cls) -> None:
        """Create a worker and patch MwClientPage."""
        self._mock_page_cls = mock_mw_client_cls

    def _set_pages(self, new_exists, new_is_redirect, old_is_redirect):
        """Configure the mock MwClientPage instances returned by the class.

        Stores the mock pages as self._mock_new_page / self._mock_old_page so
        individual tests can configure .move() / .edit() on them.
        """
        self._mock_new_page = _make_mwclient_page_mock(exists=new_exists, is_redirect=new_is_redirect)
        self._mock_new_page.title = "Template:OWID/Daily"

        self._mock_old_page = _make_mwclient_page_mock(exists=True, is_redirect=old_is_redirect)
        self._mock_old_page.title = "Template:OWID/daily"

        # Attach side_effect to .load instead of the class mock directly
        self._mock_page_cls.load.side_effect = [self._mock_new_page, self._mock_old_page]

    # ── branch: new_title does NOT exist → move ──────────────────────────

    def test_move_success(self, mock_worker: RenameOwidPagesWorker) -> None:

        self._set_pages(new_exists=False, new_is_redirect=False, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": True, "newrevid": 42}

        info = RenameInfo(10, "Template:OWID/daily", "Template:OWID/Daily")
        result = mock_worker._process_one_item(info)
        mock_worker.update_status(info)

        assert result is True
        assert len(mock_worker.result.pages_renamed) == 1
        assert len(mock_worker.result.pages_failed) == 0

    def test_move_failure(self, mock_worker: RenameOwidPagesWorker) -> None:

        self._set_pages(new_exists=False, new_is_redirect=False, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": False, "error": "permission denied"}

        info = RenameInfo(10, "Template:OWID/daily", "Template:OWID/Daily")
        result = mock_worker._process_one_item(info)
        mock_worker.update_status(info)

        assert result is False
        assert len(mock_worker.result.pages_failed) == 1

    def test_move_failure_with_details(self, mock_base_worker, mock_worker: RenameOwidPagesWorker) -> None:

        self._set_pages(new_exists=False, new_is_redirect=False, old_is_redirect=False)

        self._mock_old_page.move.return_value = {
            "success": False,
            "error": "blocked",
            "details": "Title blacklist",
        }

        info = RenameInfo(10, "Template:OWID/daily", "Template:OWID/Daily")
        result = mock_worker._process_one_item(info)
        mock_worker.update_status(info)

        assert result is False
        assert len(mock_worker.result.pages_failed) == 1

    # ── branch: new_title exists, is redirect → overwrite_translations via move ───────

    def test_target_is_redirect_overwrite_succeeds(self, mock_worker: RenameOwidPagesWorker) -> None:

        self._set_pages(new_exists=True, new_is_redirect=True, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": True, "newrevid": 99}

        info = RenameInfo(10, "Template:OWID/daily", "Template:OWID/Daily")
        result = mock_worker._process_one_item(info)
        mock_worker.update_status(info)

        assert result is True
        assert len(mock_worker.result.pages_renamed) == 1

    def test_target_is_redirect_overwrite_fails(self, mock_worker: RenameOwidPagesWorker) -> None:

        self._set_pages(new_exists=True, new_is_redirect=True, old_is_redirect=False)

        self._mock_old_page.move.return_value = {"success": False, "error": "error"}

        info = RenameInfo(10, "Template:OWID/daily", "Template:OWID/Daily")
        result = mock_worker._process_one_item(info)
        mock_worker.update_status(info)

        assert result is False
        assert len(mock_worker.result.pages_failed) == 1

    # ── branch: new_title exists, old is redirect → skip + DB update ─────

    def test_source_is_redirect_skip_and_update_db(self, mock_worker: RenameOwidPagesWorker) -> None:

        self._set_pages(new_exists=True, new_is_redirect=False, old_is_redirect=True)

        info = RenameInfo(10, "Template:OWID/daily", "Template:OWID/Daily")
        result = mock_worker._process_one_item(info)
        mock_worker.update_status(info)

        assert result is False
        assert mock_worker.result.summary.skipped_target_exists == 1
        assert len(mock_worker.result.pages_failed) == 0

    # ── branch: new_title exists, neither is redirect → redirect old ─────

    def test_both_real_pages_redirects_old_to_new(self, monkeypatch, mock_worker: RenameOwidPagesWorker) -> None:

        self._set_pages(new_exists=True, new_is_redirect=False, old_is_redirect=False)

        # Mock _redirect_old_to_new
        with monkeypatch.context() as m:
            mock_redirect = MagicMock(return_value=True)
            m.setattr(mock_worker, "_redirect_old_to_new", mock_redirect)

            info = RenameInfo(10, "Template:OWID/daily", "Template:OWID/Daily")
            result = mock_worker._process_one_item(info)
            mock_worker.update_status(info)

            mock_redirect.assert_called_once()
            call_args = mock_redirect.call_args
            # First arg is info (RenameInfo), second is old_title_page (MwClientPage), third is new_title (str)
            assert call_args[0][2] == "Template:OWID/Daily"

        assert result is True


# ── tests: _redirect_old_to_new ───────────────────────────────────────────────


class TestRedirectOldToNew:
    def test_redirect_success(self, mock_worker: RenameOwidPagesWorker) -> None:

        info = RenameInfo(namespace=10, old_title="Template:OWID/daily", new_title="Template:OWID/Daily")

        mock_page = MagicMock(name="old_title_page")
        mock_page.title = "Template:OWID/daily"
        mock_page.edit.return_value = {"success": True, "newrevid": 55}

        result = mock_worker._redirect_old_to_new(info, mock_page, "Template:OWID/Daily")
        mock_worker.update_status(info)

        assert result is True
        assert info.status == "redirected"
        assert len(mock_worker.result.pages_redirected) == 1
        assert len(mock_worker.result.pages_failed) == 0
        mock_page.edit.assert_called_once_with(
            text="#REDIRECT [[Template:OWID/Daily]]",
            summary="Redirecting to [[Template:OWID/Daily]] (capitalize first letter of OWID subpage)",
        )

    def test_redirect_failure(self, mock_worker: RenameOwidPagesWorker) -> None:
        info = RenameInfo(namespace=10, old_title="Template:OWID/daily", new_title="Template:OWID/Daily")

        mock_page = MagicMock(name="old_title_page")
        mock_page.title = "Template:OWID/daily"
        mock_page.edit.return_value = {"success": False, "error": "protected page"}

        result = mock_worker._redirect_old_to_new(info, mock_page, "Template:OWID/Daily")
        mock_worker.update_status(info)

        assert result is False
        assert info.status == "failed"
        assert len(mock_worker.result.pages_failed) == 1

    def test_redirect_failure_with_details(self, mock_worker: RenameOwidPagesWorker) -> None:
        info = RenameInfo(namespace=10, old_title="Template:OWID/daily", new_title="Template:OWID/Daily")

        mock_page = MagicMock(name="old_title_page")
        mock_page.title = "Template:OWID/daily"
        mock_page.edit.return_value = {"success": False, "error": "blocked", "details": "abuse filter"}

        result = mock_worker._redirect_old_to_new(info, mock_page, "Template:OWID/Daily")
        mock_worker.update_status(info)

        assert result is False
        assert info.status == "failed"


# ── tests: _update_template_title ─────────────────────────────────────────────


class TestUpdateTemplateTitle:
    def test_updates_title_when_record_found(self, mock_worker: RenameOwidPagesWorker, mock_template_service) -> None:
        _worker = mock_worker
        mock_record = MagicMock()
        mock_record.id = 7
        mock_template_service.get_template_by_title.return_value = mock_record

        _worker._update_template_title("Old", "New")

        mock_template_service.get_template_by_title.assert_called_once_with("Old")
        mock_template_service.update_template_data.assert_called_once_with(7, {"title": "New"})

    def test_noop_when_record_not_found(self, mock_worker: RenameOwidPagesWorker, mock_template_service) -> None:
        _worker = mock_worker
        mock_template_service.get_template_by_title.return_value = None

        _worker._update_template_title("Old", "New")

        mock_template_service.update_template_data.assert_not_called()

    def test_handles_exception_gracefully(self, mock_worker: RenameOwidPagesWorker, mock_template_service) -> None:
        _worker = mock_worker
        mock_template_service.get_template_by_title.side_effect = RuntimeError("DB down")

        _worker._update_template_title("Old", "New")

        mock_template_service.update_template_data.assert_not_called()


# ── Edge Cases ─────────────────────────────────────────────────────────────────


class TestWorkerEdgeCases:
    def test_cancel_event_set_stops_processing(
        self, mock_base_worker, mock_template_service, mock_mw_client_cls
    ) -> None:
        cancel_event = threading.Event()
        cancel_event.set()

        defaults = {"job_id": 1, "user": {"username": "tester"}, "cancel_event": cancel_event}
        _worker = RenameOwidPagesWorker(
            data=JobsRunner(**defaults),
            template_service=mock_template_service,
            mw_client_cls=mock_mw_client_cls,
        )

        # Candidates must exist, otherwise process() returns "skipped" before
        # reaching the cancellation check.
        candidate = RenameInfo(
            namespace=10,
            old_title="Template:OWID/daily",
            new_title="Template:OWID/Daily",
            full_prefix="Template:OWID/",
        )
        _worker._get_candidates = MagicMock(return_value=[candidate])

        result = _worker.process()

        assert result.status == "cancelled"
        assert result.summary.total == 1
        assert result.summary.processed == 0

    def test_no_candidates_returns_skipped_before_cancel_check(
        self, mock_base_worker, mock_template_service, mock_mw_client_cls
    ) -> None:
        cancel_event = threading.Event()
        cancel_event.set()

        defaults = {"job_id": 1, "user": {"username": "tester"}, "cancel_event": cancel_event}
        _worker = RenameOwidPagesWorker(
            data=JobsRunner(**defaults),
            template_service=mock_template_service,
            mw_client_cls=mock_mw_client_cls,
        )
        _worker._get_candidates = MagicMock(return_value=[])

        result = _worker.process()

        assert result.status == "skipped"
        assert result.note == "No pages need renaming"

    def test_module_constants(self, mock_worker: RenameOwidPagesWorker) -> None:
        assert MOVE_REASON == "Capitalize first letter of OWID subpage name"
        assert len(PREFIXES) == 2
        assert (10, "OWID/", "Template:OWID/") in PREFIXES
        assert (0, "OWID/", "OWID/") in PREFIXES
