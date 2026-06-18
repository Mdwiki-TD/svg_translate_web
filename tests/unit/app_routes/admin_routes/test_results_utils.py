"""Unit tests for src/main_app/app_routes/admin_routes/results_utils.py.

Functions to test: fix_add_svglanguages_template, fix_result_data
Constants to test: FIX_BY_JOB_TYPE
"""

from __future__ import annotations

import logging

import pytest

from src.main_app.app_routes.admin_routes.results_utils import (
    FIX_BY_JOB_TYPE,
    fix_add_svglanguages_template,
    fix_result_data,
)

SKIP_MSG = "Skipped - page content is already has {{SVGLanguages|...}}"


class TestFixAddSvglanguagesTemplate:
    """Tests for fix_add_svglanguages_template()."""

    def test_early_return_when_pages_skipped_exists(self):
        """Returns data unchanged when data already has truthy pages_skipped."""
        data = {"pages_skipped": ["already_skipped"], "pages_processed": [{"status": "completed"}]}
        result = fix_add_svglanguages_template(data)
        assert result is data
        assert result["pages_skipped"] == ["already_skipped"]

    def test_uses_templates_processed(self):
        """Prefers templates_processed over pages_processed when both exist."""
        data = {
            "templates_processed": [{"status": "completed", "title": "Template:A"}],
            "pages_processed": [{"status": "failed", "title": "Page:B"}],
        }
        result = fix_add_svglanguages_template(data)
        assert len(result["pages_success"]) == 1
        assert result["pages_success"][0]["title"] == "Template:A"

    def test_uses_pages_processed_when_no_templates_processed(self):
        """Falls back to pages_processed when templates_processed is absent."""
        data = {"pages_processed": [{"status": "completed", "title": "Page:A"}]}
        result = fix_add_svglanguages_template(data)
        assert len(result["pages_success"]) == 1
        assert result["pages_success"][0]["title"] == "Page:A"

    def test_empty_pages_processed_falls_back_to_empty_list(self):
        """Iterates over empty list when neither key is present."""
        data = {}
        result = fix_add_svglanguages_template(data)
        assert result["pages_success"] == []
        assert result["pages_failed"] == []
        assert result["pages_skipped"] == []
        assert result["pages_processed"] == []

    def test_completed_status_adds_to_success(self):
        """Page with status 'completed' goes to pages_success."""
        data = {"pages_processed": [{"status": "completed", "title": "File:OK.svg"}]}
        result = fix_add_svglanguages_template(data)
        assert result["pages_success"] == [{"status": "completed", "title": "File:OK.svg"}]
        assert result["pages_failed"] == []
        assert result["pages_skipped"] == []
        assert result["pages_processed"] == []

    def test_failed_status_adds_to_failed(self):
        """Page with status 'failed' goes to pages_failed."""
        data = {"pages_processed": [{"status": "failed", "title": "File:Bad.svg"}]}
        result = fix_add_svglanguages_template(data)
        assert result["pages_failed"] == [{"status": "failed", "title": "File:Bad.svg"}]
        assert result["pages_success"] == []
        assert result["pages_skipped"] == []

    def test_skipped_msg_match_adds_to_skipped(self):
        """Page with matching skip message goes to pages_skipped with msg."""
        data = {
            "pages_processed": [
                {
                    "status": "whatever",
                    "template_title": "File:Skipped.svg",
                    "steps": {"load_template_text": {"msg": SKIP_MSG}},
                }
            ]
        }
        result = fix_add_svglanguages_template(data)
        assert result["pages_skipped"] == [{"title": "File:Skipped.svg", "msg": SKIP_MSG}]
        assert result["pages_success"] == []
        assert result["pages_failed"] == []

    def test_unknown_status_stays_in_processed(self):
        """Page without completed/failed/skipped status remains in pages_processed."""
        data = {"pages_processed": [{"status": "pending", "title": "File:Pending.svg"}]}
        result = fix_add_svglanguages_template(data)
        assert result["pages_processed"] == [{"status": "pending", "title": "File:Pending.svg"}]
        assert result["pages_success"] == []
        assert result["pages_failed"] == []
        assert result["pages_skipped"] == []

    def test_template_title_fallback_to_title(self):
        """Uses template_title first, falls back to title for skipped entry."""
        data = {
            "pages_processed": [
                {
                    "steps": {"load_template_text": {"msg": SKIP_MSG}},
                    "template_title": "Template:Main",
                    "title": "Fallback",
                }
            ]
        }
        result = fix_add_svglanguages_template(data)
        assert result["pages_skipped"][0]["title"] == "Template:Main"

    def test_title_fallback_when_template_title_missing(self):
        """Uses title when template_title is absent for skipped entry."""
        data = {
            "pages_processed": [
                {
                    "steps": {"load_template_text": {"msg": SKIP_MSG}},
                    "title": "File:NoTemplateTitle.svg",
                }
            ]
        }
        result = fix_add_svglanguages_template(data)
        assert result["pages_skipped"][0]["title"] == "File:NoTemplateTitle.svg"

    def test_skipped_does_not_match_different_msg(self):
        """Page with different steps msg is not treated as skipped."""
        data = {
            "pages_processed": [
                {
                    "steps": {"load_template_text": {"msg": "Some other message"}},
                    "title": "File:Other.svg",
                }
            ]
        }
        result = fix_add_svglanguages_template(data)
        assert result["pages_skipped"] == []
        assert len(result["pages_processed"]) == 1

    def test_summary_counts_are_correct(self):
        """Summary dict has correct counts for success, failed, skipped."""
        data = {
            "pages_processed": [
                {"status": "completed", "title": "A"},
                {"status": "completed", "title": "B"},
                {"status": "failed", "title": "C"},
                {
                    "steps": {"load_template_text": {"msg": SKIP_MSG}},
                    "title": "D",
                },
                {"status": "unknown", "title": "E"},
            ]
        }
        result = fix_add_svglanguages_template(data)
        assert result["summary"]["success"] == 2
        assert result["summary"]["failed"] == 1
        assert result["summary"]["skipped"] == 1

    def test_summary_preserves_existing_keys(self):
        """Existing keys in summary are preserved when updating."""
        data = {"pages_processed": [], "summary": {"existing_key": "value"}}
        result = fix_add_svglanguages_template(data)
        assert result["summary"]["existing_key"] == "value"
        assert result["summary"]["success"] == 0

    def test_mixed_statuses_classify_correctly(self):
        """All pages with various statuses are classified into correct buckets."""
        data = {
            "pages_processed": [
                {"status": "completed", "title": "S1"},
                {"status": "failed", "title": "F1"},
                {"status": "completed", "title": "S2"},
                {
                    "steps": {"load_template_text": {"msg": SKIP_MSG}},
                    "title": "SK1",
                },
                {"status": "running", "title": "P1"},
                {"status": "failed", "title": "F2"},
                {"status": "completed", "title": "S3"},
            ]
        }
        result = fix_add_svglanguages_template(data)
        assert len(result["pages_success"]) == 3
        assert len(result["pages_failed"]) == 2
        assert len(result["pages_skipped"]) == 1
        assert len(result["pages_processed"]) == 1  # "running" stays
        assert result["summary"]["success"] == 3
        assert result["summary"]["failed"] == 2
        assert result["summary"]["skipped"] == 1


class TestFixResultData:
    """Tests for fix_result_data()."""

    def test_empty_dict_returns_unchanged(self):
        """Empty dict is returned immediately."""
        data: dict = {}
        result = fix_result_data(data, "add_svglanguages_template")
        assert result == {}
        assert result is data

    def test_none_returns_unchanged(self):
        """None is returned immediately."""
        result = fix_result_data(None, "add_svglanguages_template")  # type: ignore[arg-type]
        assert result is None

    def test_known_job_type_calls_fix_function(self):
        """Known job type calls the registered fix function."""
        data = {"pages_processed": [{"status": "completed", "title": "File:Test.svg"}]}
        result = fix_result_data(data, "add_svglanguages_template")
        assert result["pages_success"][0]["title"] == "File:Test.svg"
        assert result["summary"]["success"] == 1

    def test_unknown_job_type_returns_data_unchanged(self):
        """Unknown job type returns data without modification."""
        data = {"some_key": "value"}
        result = fix_result_data(data, "nonexistent_job_type")
        assert result is data
        assert result == {"some_key": "value"}

    def test_exception_in_fix_function_is_caught_and_logged(self, caplog):
        """Exception raised by fix function is caught and logged at ERROR level."""
        data = {"templates_processed": 42}

        with caplog.at_level(logging.ERROR):
            result = fix_result_data(data, "add_svglanguages_template")

        assert result is data
        assert "Error while fixing result data for job type add_svglanguages_template" in caplog.text

    def test_falsy_values_return_unchanged(self):
        """Falsy non-dict values (empty list, etc.) are returned immediately."""
        data: list = []
        result = fix_result_data(data, "add_svglanguages_template")  # type: ignore[arg-type]
        assert result == []


class TestFixByJobType:
    """Tests for the FIX_BY_JOB_TYPE registry."""

    def test_has_add_svglanguages_template_key(self):
        """Registry contains the expected key."""
        assert "add_svglanguages_template" in FIX_BY_JOB_TYPE

    def test_maps_to_correct_function(self):
        """Registry maps to fix_add_svglanguages_template function."""
        assert FIX_BY_JOB_TYPE["add_svglanguages_template"] is fix_add_svglanguages_template

    def test_is_dict(self):
        """FIX_BY_JOB_TYPE is a dict."""
        assert isinstance(FIX_BY_JOB_TYPE, dict)
