"""Tests for ``jobs.registry.load_job_data``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from src.main_app.jobs.registry import load_job_data

MODULE = "src.main_app.jobs.registry"


@dataclass
class MockRegistries:
    admins: dict[str, Any]
    public: dict[str, Any]


@pytest.fixture
def registries(monkeypatch: pytest.MonkeyPatch) -> MockRegistries:
    admins: dict[str, Any] = {}
    public: dict[str, Any] = {}
    monkeypatch.setattr(f"{MODULE}.jobs_data_admins", admins)
    monkeypatch.setattr(f"{MODULE}.jobs_data_public", public)
    return MockRegistries(admins=admins, public=public)


class TestLoadJobData:
    def test_returns_admin_job(self, registries: MockRegistries) -> None:
        marker = object()
        registries.admins["a"] = marker

        assert load_job_data("a") is marker

    def test_returns_public_job(self, registries: MockRegistries) -> None:
        marker = object()
        registries.public["p"] = marker

        assert load_job_data("p") is marker

    def test_admin_wins_when_type_is_in_both(self, registries: MockRegistries) -> None:
        admin_marker, public_marker = object(), object()
        registries.admins["same"] = admin_marker
        registries.public["same"] = public_marker

        assert load_job_data("same") is admin_marker

    def test_unknown_type_returns_none(self, registries: MockRegistries) -> None:
        assert load_job_data("missing") is None
