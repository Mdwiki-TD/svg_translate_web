"""Unit tests for add_svglanguages_template worker module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ── Module-level monkeypatch fixtures ────────────────────────────────────────


@pytest.fixture
def mock_add_svglanguages_services(monkeypatch: pytest.MonkeyPatch, mock_base_worker):
    """Mock the services used by add_svglanguages_template worker."""

    _mock_class = MagicMock()
    _mock_class.return_value = MagicMock()

    mocks = {
        "RE_SVG_LANG": MagicMock(),
        "MwClientPage": MagicMock(),
        "add_template_to_text": MagicMock(),
        "list_templates": MagicMock(),
        "AddSvgSVGLanguagesTemplate": _mock_class,
        "get_user_site": mock_base_worker["get_user_site"],
    }

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.RE_SVG_LANG",
        mocks["RE_SVG_LANG"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.MwClientPage",
        mocks["MwClientPage"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.add_template_to_text",
        mocks["add_template_to_text"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker.list_templates",
        mocks["list_templates"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.runner.AddSvgSVGLanguagesTemplate",
        mocks["AddSvgSVGLanguagesTemplate"],
    )
    return mocks
