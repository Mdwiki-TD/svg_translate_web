"""Tests for helper functions in src.main_app.app_routes.tasks.routes."""

from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.app_routes.tasks.routes import (
    format_task_message,
    get_disable_uploads,
    load_state_hash,
)


# ---------------------------------------------------------------------------
# get_disable_uploads
# ---------------------------------------------------------------------------


class TestGetDisableUploads:
    """Tests for the get_disable_uploads helper."""

    def test_returns_settings_value(self, monkeypatch):
        """get_disable_uploads returns settings.disable_uploads."""
        fake_settings = types.SimpleNamespace(disable_uploads="1")
        monkeypatch.setattr("src.main_app.app_routes.tasks.routes.settings", fake_settings)

        assert get_disable_uploads() == "1"

    def test_returns_empty_string_when_not_set(self, monkeypatch):
        """get_disable_uploads returns empty string when not configured."""
        fake_settings = types.SimpleNamespace(disable_uploads="")
        monkeypatch.setattr("src.main_app.app_routes.tasks.routes.settings", fake_settings)

        assert get_disable_uploads() == ""

    def test_returns_zero_string(self, monkeypatch):
        """get_disable_uploads returns '0' when configured with '0'."""
        fake_settings = types.SimpleNamespace(disable_uploads="0")
        monkeypatch.setattr("src.main_app.app_routes.tasks.routes.settings", fake_settings)

        assert get_disable_uploads() == "0"


# ---------------------------------------------------------------------------
# load_state_hash
# ---------------------------------------------------------------------------


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.secret_key = "test-secret"
    return app


class TestLoadStateHash:
    """Tests for the load_state_hash helper."""

    def test_returns_tuple_of_int_and_str(self, flask_app):
        """load_state_hash returns (refresh_count, state_hash) tuple."""
        with flask_app.test_request_context("/task/abc"):
            count, state_hash = load_state_hash(None, [])
        assert isinstance(count, int)
        assert isinstance(state_hash, str)

    def test_state_hash_length(self, flask_app):
        """state_hash is exactly 8 characters (truncated sha256 hexdigest)."""
        with flask_app.test_request_context("/task/abc"):
            _, state_hash = load_state_hash({"status": "Running", "updated_at": "2024-01-01"}, [])
        assert len(state_hash) == 8

    def test_refresh_count_starts_at_zero_first_call(self, flask_app):
        """refresh_count is 0 on first call with no query params."""
        with flask_app.test_request_context("/task/abc"):
            count, _ = load_state_hash({"status": "Running", "updated_at": "t"}, [])
        assert count == 0

    def test_refresh_count_increments_when_state_unchanged(self, flask_app):
        """refresh_count increments when prev state_hash matches current hash."""
        task = {"status": "Running", "updated_at": "t"}
        stages = []
        with flask_app.test_request_context("/task/abc"):
            _, state_hash = load_state_hash(task, stages)

        # On subsequent request with matching state_hash and refresh_count=0
        with flask_app.test_request_context(f"/task/abc?state_hash={state_hash}&refresh_count=0"):
            count, new_hash = load_state_hash(task, stages)

        assert new_hash == state_hash
        assert count == 1

    def test_refresh_count_resets_when_state_changes(self, flask_app):
        """refresh_count resets to 0 when state changes."""
        task_v1 = {"status": "Running", "updated_at": "t1"}
        task_v2 = {"status": "Completed", "updated_at": "t2"}

        with flask_app.test_request_context("/task/abc"):
            _, hash_v1 = load_state_hash(task_v1, [])

        # Pass old hash but task state has changed
        with flask_app.test_request_context(f"/task/abc?state_hash={hash_v1}&refresh_count=5"):
            count, hash_v2 = load_state_hash(task_v2, [])

        assert hash_v1 != hash_v2
        assert count == 0

    def test_none_task_produces_empty_status(self, flask_app):
        """load_state_hash handles None task gracefully."""
        with flask_app.test_request_context("/task/abc"):
            count, state_hash = load_state_hash(None, [])
        assert len(state_hash) == 8

    def test_stages_included_in_hash(self, flask_app):
        """Hash changes when stages change."""
        task = {"status": "Running", "updated_at": "t"}
        stages_empty = []
        stages_with_data = [("stage1", {"status": "done", "message": "ok", "sub_name": "", "updated_at": "t"})]

        with flask_app.test_request_context("/task/abc"):
            _, hash_empty = load_state_hash(task, stages_empty)

        with flask_app.test_request_context("/task/abc"):
            _, hash_with = load_state_hash(task, stages_with_data)

        assert hash_empty != hash_with

    def test_same_state_produces_same_hash(self, flask_app):
        """Same task state always produces the same hash."""
        task = {"status": "Running", "updated_at": "2024-01-01T00:00:00"}
        stages = [("extract", {"status": "done", "message": "x", "sub_name": "", "updated_at": "t"})]

        with flask_app.test_request_context("/task/abc"):
            _, hash1 = load_state_hash(task, stages)

        with flask_app.test_request_context("/task/abc"):
            _, hash2 = load_state_hash(task, stages)

        assert hash1 == hash2


# ---------------------------------------------------------------------------
# format_task_message
# ---------------------------------------------------------------------------


class TestFormatTaskMessage:
    """Tests for the format_task_message helper."""

    def test_replaces_commas_with_br_in_stage_messages(self):
        """format_task_message replaces commas with <br> in stage messages."""
        formatted = [
            {
                "stages": {
                    "extract": {"message": "Files: 10, Fixed: 5, Not fixed: 2"},
                }
            }
        ]
        result = format_task_message(formatted)
        assert "<br>" in result[0]["stages"]["extract"]["message"]
        assert "," not in result[0]["stages"]["extract"]["message"]

    def test_tasks_without_stages_unchanged(self):
        """format_task_message leaves tasks without stages untouched."""
        formatted = [{"status": "Running"}]
        result = format_task_message(formatted)
        assert result == [{"status": "Running"}]

    def test_returns_same_list_reference(self):
        """format_task_message modifies and returns the same list."""
        formatted = [{"stages": {"s1": {"message": "a,b"}}}]
        result = format_task_message(formatted)
        assert result is formatted