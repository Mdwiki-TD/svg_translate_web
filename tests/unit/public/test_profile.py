"""Unit tests for src/main_app/public/profile.py."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.main_app.public.profile import ProfileRoutes


class MockUser:
    def __init__(self, username: str = "testuser", is_active_admin: bool = False) -> None:
        self.username = username
        self.is_active_admin = is_active_admin


MOCK_JOBS_DATA_PUBLIC: dict[str, MagicMock] = {
    "job_type_1": MagicMock(),
    "job_type_2": MagicMock(),
}

DEFAULT_STATS: dict[str, Any] = {
    "stats": {"total": 10, "completed": 5, "failed": 2, "cancelled": 1},
    "recent_jobs": [
        {"id": 1, "job_type": "job_type_1", "status": "completed"},
        {"id": 2, "job_type": "job_type_2", "status": "failed"},
    ],
}

EMPTY_STATS: dict[str, Any] = {
    "stats": {"total": 0, "completed": 0, "failed": 0, "cancelled": 0},
    "recent_jobs": [],
}

TEMPLATE_TEXT = (
    "username={{ username|default('__NONE__') }}|"
    "stats_total={{ stats.total if stats is defined else '__NONE__' }}|"
    "stats_completed={{ stats.completed if stats is defined else '__NONE__' }}|"
    "stats_failed={{ stats.failed if stats is defined else '__NONE__' }}|"
    "stats_cancelled={{ stats.cancelled if stats is defined else '__NONE__' }}|"
    "recent_jobs={{ recent_jobs if recent_jobs is defined else '__NONE__' }}|"
    "jobs_data_public={{ jobs_data_public if jobs_data_public is defined else '__NONE__' }}"
)


@pytest.fixture(autouse=True)
def setup_db():
    """Override conftest's autouse setup_db — no database needed for profile unit tests."""


@pytest.fixture
def app(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "profile.html").write_text(TEMPLATE_TEXT)
    app = Flask(__name__, template_folder=str(templates_dir))
    app.secret_key = "test"
    bp_profile = Blueprint("profile", __name__, url_prefix="/profile")
    app.register_blueprint(ProfileRoutes(bp_profile).bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _mock_jobs_data_public(monkeypatch):
    monkeypatch.setattr(
        "src.main_app.public.profile.jobs_data_public",
        MOCK_JOBS_DATA_PUBLIC,
    )


@pytest.fixture(autouse=True)
def _mock_stats_functions(monkeypatch):
    mock_get_all = MagicMock(return_value=DEFAULT_STATS)
    mock_get_user = MagicMock(return_value=DEFAULT_STATS)
    monkeypatch.setattr(
        "src.main_app.public.profile.JobsService.get_all_user_jobs_stats",
        mock_get_all,
    )
    monkeypatch.setattr(
        "src.main_app.public.profile.JobsService.get_user_jobs_stats",
        mock_get_user,
    )
    return mock_get_all, mock_get_user


class TestDashboard:
    def test_dashboard_without_username_and_logged_in(
        self,
        client,
        monkeypatch,
        _mock_stats_functions,
    ):
        mock_get_all, _ = _mock_stats_functions
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="alice"),
        )
        resp = client.get("/profile/")
        assert resp.status_code == 200
        mock_get_all.assert_called_once_with("alice")
        assert b"username=alice" in resp.data

    def test_dashboard_without_username_and_not_logged_in(
        self,
        client,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: None,
        )
        resp = client.get("/profile/")
        assert resp.status_code == 200
        with client.session_transaction() as session:
            flashes = session.get("_flashes", [])
            assert any(cat == "warning" and "must be logged in" in msg for cat, msg in flashes)

    def test_dashboard_with_username_and_admin(
        self,
        client,
        monkeypatch,
        _mock_stats_functions,
    ):
        mock_get_all, _ = _mock_stats_functions
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="admin", is_active_admin=True),
        )
        resp = client.get("/profile/other_user")
        assert resp.status_code == 200
        mock_get_all.assert_called_once_with("other_user")
        assert b"username=other_user" in resp.data

    def test_dashboard_with_username_and_non_admin(
        self,
        client,
        monkeypatch,
        _mock_stats_functions,
    ):
        _, mock_get_user = _mock_stats_functions
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="regular_user"),
        )
        resp = client.get("/profile/other_user")
        assert resp.status_code == 200
        mock_get_user.assert_called_once()
        args, kwargs = mock_get_user.call_args
        assert kwargs["username"] == "other_user"
        assert kwargs["jobs_types"] == ["job_type_1", "job_type_2"]
        assert b"username=other_user" in resp.data

    def test_dashboard_exception_handling(
        self,
        client,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="alice"),
        )
        mock_get_all = MagicMock(side_effect=ValueError("DB connection failed"))
        monkeypatch.setattr(
            "src.main_app.public.profile.JobsService.get_all_user_jobs_stats",
            mock_get_all,
        )
        resp = client.get("/profile/")
        assert resp.status_code == 200
        assert b"stats_total=0" in resp.data
        with client.session_transaction() as session:
            flashes = session.get("_flashes", [])
            assert any(cat == "danger" and "Unable to load" in msg for cat, msg in flashes)

    def test_dashboard_renders_correct_template_variables(
        self,
        client,
        monkeypatch,
    ):
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="alice"),
        )
        resp = client.get("/profile/")
        assert resp.status_code == 200
        body = resp.data.decode()
        assert "username=alice" in body
        assert "stats_total=10" in body
        assert "stats_completed=5" in body
        assert "stats_failed=2" in body
        assert "stats_cancelled=1" in body
        assert "recent_jobs=[" in body
        assert "&#39;job_type_1&#39;" in body
        assert "&#39;job_type_2&#39;" in body
        assert "jobs_data_public=[&#39;job_type_1&#39;" in body
