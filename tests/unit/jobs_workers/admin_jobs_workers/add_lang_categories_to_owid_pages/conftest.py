"""Fixtures for add_lang_categories_to_owid_pages tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_lang_categories_services(monkeypatch: pytest.MonkeyPatch, mock_base_worker):
    """Mock the services used by add_lang_categories_to_owid_pages worker."""

    _mock_class = MagicMock()
    _mock_class.return_value = MagicMock()

    mocks = {
        "MwClientPage": MagicMock(),
        "get_file_languages": MagicMock(return_value={"error": None, "langs": ["en", "ja", "ar"]}),
        "AddLangCategoriesWorker": _mock_class,
        "get_user_site": mock_base_worker["get_user_site"],
    }

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_lang_categories_to_owid_pages.worker.MwClientPage",
        mocks["MwClientPage"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_lang_categories_to_owid_pages.worker.get_file_languages",
        mocks["get_file_languages"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_lang_categories_to_owid_pages.runner.AddLangCategoriesWorker",
        mocks["AddLangCategoriesWorker"],
    )
    return mocks
