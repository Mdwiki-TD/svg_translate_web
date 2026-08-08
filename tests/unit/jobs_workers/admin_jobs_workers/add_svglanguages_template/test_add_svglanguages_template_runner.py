"""Unit tests for add_svglanguages_template worker module."""

from __future__ import annotations

import threading

from src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.runner import (
    add_svglanguages_template_to_templates,
)
from src.main_app.jobs_workers.objects import JobsRunner


class TestAddSvgSVGLanguagesTemplateToTemplates:
    """Tests for the add_svglanguages_template_to_templates function."""

    def test_function_creates_and_runs_worker(self, mock_add_svglanguages_services):
        """Test that the function creates and runs a worker."""
        mock_worker_class = mock_add_svglanguages_services["AddSvgSVGLanguagesTemplate"]
        mock_worker_instance = mock_worker_class.return_value

        user = {"username": "test_user"}
        cancel_event = threading.Event()

        runner_data = JobsRunner(job_id=1, user=user, cancel_event=cancel_event)
        add_svglanguages_template_to_templates(runner_data)

        mock_worker_class.assert_called_once_with(job_id=1, user=user, cancel_event=cancel_event, args=None)
        mock_worker_instance.run.assert_called_once()

    def test_function_accepts_args_keyword_param(self, mock_add_svglanguages_services):
        """Test that the entry point accepts args= keyword-only param (unified signature)."""
        mock_worker_class = mock_add_svglanguages_services["AddSvgSVGLanguagesTemplate"]
        mock_worker_instance = mock_worker_class.return_value

        runner_data = JobsRunner(job_id=1, user={}, args={"some_key": "some_value"})
        add_svglanguages_template_to_templates(runner_data)

        mock_worker_instance.run.assert_called_once()

    def test_function_args_defaults_to_none(self, mock_add_svglanguages_services):
        """Test that args defaults to None and the entry point works without it."""
        mock_worker_class = mock_add_svglanguages_services["AddSvgSVGLanguagesTemplate"]
        mock_worker_instance = mock_worker_class.return_value

        runner_data = JobsRunner(job_id=2, user={})
        add_svglanguages_template_to_templates(runner_data)

        mock_worker_class.assert_called_once_with(job_id=2, user={}, cancel_event=None, args=None)
        mock_worker_instance.run.assert_called_once()

    def test_function_maps_limit_items(self, mock_add_svglanguages_services):
        """Test that limit_items is mapped to limit_items in args."""
        mock_worker_class = mock_add_svglanguages_services["AddSvgSVGLanguagesTemplate"]

        runner_data = JobsRunner(job_id=1, user={}, args={"limit_items": 10})
        add_svglanguages_template_to_templates(runner_data)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"]["limit_items"] == 10

    def test_function_does_not_map_when_key_absent(self, mock_add_svglanguages_services):
        """Test that args are passed unchanged when limit_items is absent."""
        mock_worker_class = mock_add_svglanguages_services["AddSvgSVGLanguagesTemplate"]

        runner_data = JobsRunner(job_id=1, user={}, args={"other_key": "value"})
        add_svglanguages_template_to_templates(runner_data)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert "limit_items" not in call_kwargs["args"]

    def test_function_does_not_modify_args_when_args_is_none(self, mock_add_svglanguages_services):
        """Test that entry point works correctly when args is None."""
        mock_worker_class = mock_add_svglanguages_services["AddSvgSVGLanguagesTemplate"]

        runner_data = JobsRunner(job_id=1, user={}, args=None)
        add_svglanguages_template_to_templates(runner_data)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"] is None
