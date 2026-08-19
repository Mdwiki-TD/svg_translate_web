"""Unit tests for src/main_app/jobs/base_worker.py (test_base_worker.py)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.base_worker import BaseObjectsJobWorker
from src.main_app.jobs_workers.objects import JobsRunner


class _ConcreteWorker(BaseObjectsJobWorker):
    """Minimal concrete subclass for testing base-class methods."""

    def get_job_type(self) -> str:
        return "test_worker"

    def process(self):  # pragma: no cover – not exercised here
        return self.result


class TestBaseObjectsJobWorkerAbstract:
    def test_cannot_instantiate_without_methods(self):
        with pytest.raises(TypeError):
            BaseObjectsJobWorker(
                JobsRunner(
                    job_id=1,
                    user={},
                    cancel_event=None,
                )
            )  # type: ignore


# ── _validate_user_permissions ─────────────────────────────────────────────


class TestValidateUserPermissions:
    @staticmethod
    def _make_worker() -> _ConcreteWorker:
        return _ConcreteWorker(JobsRunner(job_id=1, user={}, cancel_event=None))

    def test_returns_true_when_site_has_autopatrol(self, mock_site: MagicMock) -> None:
        worker = self._make_worker()
        worker.site = mock_site  # rights already includes "autopatrol"

        assert worker._validate_user_permissions() is True
        assert worker.result.status == "pending"  # status unchanged

    def test_returns_false_when_autopatrol_missing(self) -> None:
        worker = self._make_worker()
        site = MagicMock(name="mw_site")
        site.username = "noperm_user"
        site.rights = ["edit", "upload"]  # no autopatrol
        worker.site = site

        assert worker._validate_user_permissions() is False
        assert worker.result.status == "failed"
        assert any("autopatrol" in e["error"] for e in worker.result.errors)
        assert worker.result.errors[-1]["error_type"] == "PermissionError"

    def test_returns_false_when_site_is_none(self) -> None:
        worker = self._make_worker()
        worker.site = None

        assert worker._validate_user_permissions() is False
        # status is NOT changed (no explicit failure set for missing site here)
        assert worker.result.status == "pending"

    def test_error_message_includes_username(self) -> None:
        worker = self._make_worker()
        site = MagicMock(name="mw_site")
        site.username = "alice"
        site.rights = []
        worker.site = site

        worker._validate_user_permissions()

        assert any("alice" in e["error"] for e in worker.result.errors)

    def test_empty_rights_list(self) -> None:
        worker = self._make_worker()
        site = MagicMock(name="mw_site")
        site.username = "user"
        site.rights = []
        worker.site = site

        assert worker._validate_user_permissions() is False
        assert worker.result.status == "failed"

    def test_multiple_errors_accumulate(self) -> None:
        """Calling _validate_user_permissions twice appends an error each time."""
        worker = self._make_worker()
        site = MagicMock(name="mw_site")
        site.username = "user"
        site.rights = ["edit"]
        worker.site = site

        worker._validate_user_permissions()
        worker._validate_user_permissions()

        perm_errors = [e for e in worker.result.errors if e["error_type"] == "PermissionError"]
        assert len(perm_errors) == 2
