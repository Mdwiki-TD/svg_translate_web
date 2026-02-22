"""Tests for category helpers."""

from __future__ import annotations

import types

import pytest

from src.main_app.app_routes.templates import category


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.app.app_routes.templates.category.settings", types.SimpleNamespace(oauth=types.SimpleNamespace(user_agent="agent")))


def test_get_category_members_api_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        def __init__(self, pages):
            self._pages = pages
            self.status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return self._pages

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.calls = []

        def get(self, url, params=None, timeout=None):
            self.calls.append((url, params, timeout))
            if "cmcontinue" in params:
                return DummyResponse({"query": {"categorymembers": []}})
            return DummyResponse(
                {
                    "continue": {"cmcontinue": "next"},
                    "query": {"categorymembers": [{"title": "Page"}]},
                }
            )

    monkeypatch.setattr("src.app.app_routes.templates.category.requests.Session", DummySession)

    pages = category.get_category_members_api("Category:Example", "commons.wikimedia.org")

    assert pages == ["Page"]


def test_get_category_members_petscan(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        text = "Page\nAnother"

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr("src.app.app_routes.templates.category.requests.get", lambda url, headers=None, timeout=None: DummyResponse())

    pages = category.get_category_members_petscan("Category:Example", "commons.wikimedia.org")

    assert pages == ["Page", "Another"]


def test_get_category_members_prefers_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.app.app_routes.templates.category.get_category_members_api", lambda *args, **kwargs: ["Page1"])
    monkeypatch.setattr("src.app.app_routes.templates.category.get_category_members_petscan", lambda *args, **kwargs: ["Page2"])

    pages = category.get_category_members()

    assert pages == ["Page1"]
