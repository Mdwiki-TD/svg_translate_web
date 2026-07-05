"""
conftest for unit tests
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ── jobs_workers fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_before_run(monkeypatch: pytest.MonkeyPatch):
    # Bypass BaseObjectsJobWorker.before_run
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.BaseObjectsJobWorker.before_run", MagicMock(return_value=True)
    )


@pytest.fixture
def mock_base_worker(monkeypatch: pytest.MonkeyPatch):
    """Mock services common to both workers."""
    mocks = {
        "generate_result_file_name": MagicMock(side_effect=lambda jid, jtype: f"{jtype}_job_{jid}.json"),
        "get_user_site": MagicMock(return_value=MagicMock(name="mw_site")),
        "save_job_result_by_name": MagicMock(),
        "update_job_status": MagicMock(),
        "update_job_status_with_retry": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name", mocks["save_job_result_by_name"]
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.get_user_site",
        mocks["get_user_site"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status_with_retry",
        mocks["update_job_status_with_retry"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status",
        mocks["update_job_status"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.generate_result_file_name", mocks["generate_result_file_name"]
    )
    return mocks
