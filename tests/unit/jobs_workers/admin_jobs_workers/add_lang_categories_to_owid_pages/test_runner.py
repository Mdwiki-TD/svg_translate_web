"""Unit tests for add_lang_categories_to_owid_pages runner module."""

from __future__ import annotations

import threading

from src.main_app.jobs_workers.admin_jobs_workers.add_lang_categories_to_owid_pages.runner import (
    add_lang_categories_to_owid_pages_entry,
)


class TestAddLangCategoriesRunner:
    def test_function_creates_and_runs_worker(self, mock_lang_categories_services):
        mock_worker_class = mock_lang_categories_services["AddLangCategoriesWorker"]
        mock_worker_instance = mock_worker_class.return_value

        user = {"username": "test_user"}
        cancel_event = threading.Event()

        add_lang_categories_to_owid_pages_entry(job_id=1, user=user, cancel_event=cancel_event)

        mock_worker_class.assert_called_once_with(job_id=1, user=user, cancel_event=cancel_event, args=None)
        mock_worker_instance.run.assert_called_once()

    def test_function_accepts_args_keyword_param(self, mock_lang_categories_services):
        mock_worker_class = mock_lang_categories_services["AddLangCategoriesWorker"]
        mock_worker_instance = mock_worker_class.return_value

        add_lang_categories_to_owid_pages_entry(job_id=1, user=None, args={"limit_items": 10})

        mock_worker_class.assert_called_once_with(job_id=1, user=None, cancel_event=None, args={"limit_items": 10})
        mock_worker_instance.run.assert_called_once()

    def test_function_args_defaults_to_none(self, mock_lang_categories_services):
        mock_worker_class = mock_lang_categories_services["AddLangCategoriesWorker"]
        mock_worker_instance = mock_worker_class.return_value

        add_lang_categories_to_owid_pages_entry(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(job_id=2, user=None, cancel_event=None, args=None)
        mock_worker_instance.run.assert_called_once()
