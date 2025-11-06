"""Tests for templates routes utilities."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from src.app.app_routes.templates import routes


@pytest.fixture(autouse=True)
def patch_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    monkeypatch.setattr(routes, "settings", types.SimpleNamespace(paths=types.SimpleNamespace(svg_data=str(svg_dir))))
    return svg_dir


def test_get_main_data_reads_file(tmp_path: Path) -> None:
    title_dir = tmp_path / "svg" / "topic"
    title_dir.mkdir(parents=True)
    payload = {"value": 1}
    (title_dir / "files_stats.json").write_text(json.dumps(payload), encoding="utf-8")

    assert routes.get_main_data("topic") == payload


def test_temp_data_sanitizes_name(tmp_path: Path) -> None:
    sanitized = "template_clean_name"
    (tmp_path / "svg" / sanitized).mkdir(parents=True)

    result = routes.temp_data("Template:Clean Name!")

    assert result["title_dir"] == sanitized


def test_temps_main_files_falls_back_to_main_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    template_entry = {"Sample": {"title_dir": "sample"}}
    monkeypatch.setattr(routes, "get_templates_db", lambda: types.SimpleNamespace(list=lambda: []))
    monkeypatch.setattr(routes, "add_or_update_template", lambda title, main_file: None)
    monkeypatch.setattr(routes, "get_main_data", lambda title: {"main_title": "Example.svg"})

    data = routes.temps_main_files(template_entry)

    assert data["Sample"]["main_file"] == "File:Example.svg"
