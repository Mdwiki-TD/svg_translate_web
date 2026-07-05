from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_base_worker):
    """Mock the services used by create_owid_pages worker."""

    mock_page_instance = MagicMock()

    mocks = {
        "is_job_cancelled": MagicMock(return_value=False),
        "list_templates": MagicMock(),
        "MwClientPage": MagicMock(),
        "create_new_text": MagicMock(),
        "is_pages_exists": MagicMock(return_value={}),
        "merge_categories": MagicMock(side_effect=lambda current, new: new),
        "sort_categories": MagicMock(side_effect=lambda text: text),
        "is_job_cancelled_file_exist": MagicMock(return_value=False),
        "page_instance": mock_page_instance,
        "get_user_site": mock_base_worker["get_user_site"],
    }

    mocks["MwClientPage"].return_value = mock_page_instance

    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled",
        mocks["is_job_cancelled"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled_file_exist",
        mocks["is_job_cancelled_file_exist"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.list_templates",
        mocks["list_templates"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.MwClientPage",
        mocks["MwClientPage"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.create_new_text",
        mocks["create_new_text"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.is_pages_exists",
        mocks["is_pages_exists"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.merge_categories",
        mocks["merge_categories"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.sort_categories",
        mocks["sort_categories"],
    )

    return mocks
