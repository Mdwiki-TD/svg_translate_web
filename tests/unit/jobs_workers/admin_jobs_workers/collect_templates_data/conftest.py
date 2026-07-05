from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_find_last_world(monkeypatch: pytest.MonkeyPatch):
    """Mock find_newest_world_file to return None by default."""
    mock = MagicMock(return_value=None)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
        mock,
    )
    return mock


@pytest.fixture
def mock_find_source(monkeypatch: pytest.MonkeyPatch):
    """Mock find_template_source to return empty string by default."""
    mock = MagicMock(return_value="")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_template_source",
        mock,
    )
    return mock


@pytest.fixture
def mock_services(mock_before_run, monkeypatch: pytest.MonkeyPatch, tmp_path, mock_base_worker):
    """Mock the services used by collect_templates_data_worker."""

    mocks = {
        "list_templates": MagicMock(),
        "add_template_data": MagicMock(),
        "update_template_data": MagicMock(),
        "update_job_status": MagicMock(),
        "save_job_result_by_name": MagicMock(return_value=str(tmp_path / "job_1.json")),
        "get_category_members": MagicMock(),
        "MwClientPage": MagicMock(),
        "find_main_title": MagicMock(),
        "get_chart_by_slug": MagicMock(),
        "fetch_grapher_metadata": MagicMock(return_value=None),
        "get_user_site": mock_base_worker["get_user_site"],
    }

    mock_template_service = MagicMock()
    mock_template_service.list_templates = mocks["list_templates"]
    mock_template_service.add_template_data = mocks["add_template_data"]
    mock_template_service.update_template_data = mocks["update_template_data"]
    mock_template_service.get_template_by_title = MagicMock()

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.TemplateService",
        MagicMock(return_value=mock_template_service),
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status",
        mocks["update_job_status"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mocks["save_job_result_by_name"],
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.get_category_members",
        mocks["get_category_members"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.MwClientPage",
        mocks["MwClientPage"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_main_title",
        mocks["find_main_title"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.get_chart_by_slug",
        mocks["get_chart_by_slug"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.fetch_grapher_metadata",
        mocks["fetch_grapher_metadata"],
    )

    return mocks
