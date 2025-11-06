"""Tests for admin access decorator."""

from __future__ import annotations

import types

import pytest

from src.app.app_routes.admin import admins_required


def test_admin_required_redirects_when_not_logged_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admins_required, "current_user", lambda: None)
    monkeypatch.setattr(admins_required, "redirect", lambda location: f"redirect:{location}")
    monkeypatch.setattr(admins_required, "url_for", lambda endpoint: f"/{endpoint}")

    @admins_required.admin_required
    def view() -> str:
        return "ok"

    assert view() == "redirect:/auth.login"


def test_admin_required_blocks_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admins_required, "current_user", lambda: types.SimpleNamespace(username="user"))
    monkeypatch.setattr(admins_required, "active_coordinators", lambda: [])

    class AbortCalled(Exception):
        pass

    def fake_abort(code: int) -> None:
        raise AbortCalled(code)

    monkeypatch.setattr(admins_required, "abort", fake_abort)

    @admins_required.admin_required
    def view() -> str:
        return "ok"

    with pytest.raises(AbortCalled) as excinfo:
        view()

    assert excinfo.value.args[0] == 403


def test_admin_required_allows_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admins_required, "current_user", lambda: types.SimpleNamespace(username="boss"))
    monkeypatch.setattr(admins_required, "active_coordinators", lambda: ["boss"])

    @admins_required.admin_required
    def view() -> str:
        return "ok"

    assert view() == "ok"
