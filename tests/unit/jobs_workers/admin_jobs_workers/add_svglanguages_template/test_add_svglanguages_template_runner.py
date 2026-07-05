"""Unit tests for add_svglanguages_template worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.runner import (
    add_svglanguages_template_to_templates,
)

# ── Module-level monkeypatch fixtures ────────────────────────────────────────


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_base_worker):
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


class TestAddSvgSVGLanguagesTemplateToTemplates:
    """Tests for the add_svglanguages_template_to_templates function."""

    def test_function_creates_and_runs_worker(self, mock_services):
        """Test that the function creates and runs a worker."""
        mock_worker_class = mock_services["AddSvgSVGLanguagesTemplate"]
        mock_worker_instance = mock_worker_class.return_value

        user = {"username": "test_user"}
        cancel_event = threading.Event()

        add_svglanguages_template_to_templates(job_id=1, user=user, cancel_event=cancel_event)

        mock_worker_class.assert_called_once_with(job_id=1, user=user, cancel_event=cancel_event, args=None)
        mock_worker_instance.run.assert_called_once()

    def test_function_accepts_args_keyword_param(self, mock_services):
        """Test that the entry point accepts args= keyword-only param (unified signature)."""
        mock_worker_class = mock_services["AddSvgSVGLanguagesTemplate"]
        mock_worker_instance = mock_worker_class.return_value

        # Should not raise TypeError; args is accepted but unused
        add_svglanguages_template_to_templates(job_id=1, user=None, args={"some_key": "some_value"})

        mock_worker_instance.run.assert_called_once()

    def test_function_args_defaults_to_none(self, mock_services):
        """Test that args defaults to None and the entry point works without it."""
        mock_worker_class = mock_services["AddSvgSVGLanguagesTemplate"]
        mock_worker_instance = mock_worker_class.return_value

        # Call with no args param at all
        add_svglanguages_template_to_templates(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(job_id=2, user=None, cancel_event=None, args=None)
        mock_worker_instance.run.assert_called_once()

    def test_function_maps_limit_items(self, mock_services):
        """Test that limit_items is mapped to limit_items in args."""
        mock_worker_class = mock_services["AddSvgSVGLanguagesTemplate"]

        add_svglanguages_template_to_templates(
            job_id=1,
            user=None,
            args={"limit_items": 10},
        )

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"]["limit_items"] == 10

    def test_function_does_not_map_when_key_absent(self, mock_services):
        """Test that args are passed unchanged when limit_items is absent."""
        mock_worker_class = mock_services["AddSvgSVGLanguagesTemplate"]

        add_svglanguages_template_to_templates(
            job_id=1,
            user=None,
            args={"other_key": "value"},
        )

        call_kwargs = mock_worker_class.call_args.kwargs
        assert "limit_items" not in call_kwargs["args"]

    def test_function_does_not_modify_args_when_args_is_none(self, mock_services):
        """Test that entry point works correctly when args is None."""
        mock_worker_class = mock_services["AddSvgSVGLanguagesTemplate"]

        add_svglanguages_template_to_templates(job_id=1, user=None, args=None)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"] is None
