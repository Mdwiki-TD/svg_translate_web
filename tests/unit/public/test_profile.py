"""Unit tests for src/main_app/public/profile.py."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from flask import Flask

from src.main_app.db.services import JobsService
from src.main_app.public.profile import ProfileRoutes


class MockUser:
    def __init__(self, username: str = "testuser", is_active_admin: bool = False) -> None:
        self.username = username
        self.is_active_admin = is_active_admin


MOCK_JOBS_DATA_PUBLIC: dict[str, MagicMock] = {
    "job_type_1": MagicMock(),
    "job_type_2": MagicMock(),
}


@pytest.fixture(autouse=True)
def _mock_jobs_data_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.main_app.public.profile.jobs_data_public",
        MOCK_JOBS_DATA_PUBLIC,
    )


@pytest.fixture
def seeded_jobs() -> None:
    svc = JobsService()
    svc.create_job("job_type_1", "alice")
    svc.create_job("job_type_2", "alice")
    svc.create_job("job_type_3", "other_user")


class TestDashboard:
    def test_dashboard_without_username_and_logged_in(
        self,
        mock_client: Flask.test_client,
        monkeypatch: pytest.MonkeyPatch,
        seeded_jobs: None,
    ) -> None:
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="alice"),
        )
        resp = mock_client.get("/profile/")
        assert resp.status_code == 200
        assert b"alice" in resp.data

    def test_dashboard_without_username_and_not_logged_in(
        self,
        mock_client: Flask.test_client,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: None,
        )
        resp = mock_client.get("/profile/")
        assert resp.status_code == 200

    def test_dashboard_with_username_and_admin(
        self,
        mock_client: Flask.test_client,
        monkeypatch: pytest.MonkeyPatch,
        seeded_jobs: None,
    ) -> None:
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="admin", is_active_admin=True),
        )
        resp = mock_client.get("/profile/other_user")
        assert resp.status_code == 200
        assert b"other_user" in resp.data

    def test_dashboard_with_username_and_non_admin(
        self,
        mock_client: Flask.test_client,
        monkeypatch: pytest.MonkeyPatch,
        seeded_jobs: None,
    ) -> None:
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="regular_user"),
        )
        resp = mock_client.get("/profile/other_user")
        assert resp.status_code == 200
        assert b"other_user" in resp.data

    def test_dashboard_renders_correct_template_variables(
        self,
        mock_client: Flask.test_client,
        monkeypatch: pytest.MonkeyPatch,
        seeded_jobs: None,
    ) -> None:
        monkeypatch.setattr(
            "src.main_app.public.profile.load_user",
            lambda: MockUser(username="alice"),
        )
        resp = mock_client.get("/profile/")
        assert resp.status_code == 200
        assert b"alice" in resp.data
