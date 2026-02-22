"""Tests for explorer utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.main_app.app_routes.explorer import utils


@pytest.fixture(autouse=True)
def patch_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    svg_dir = tmp_path / "svg"
    thumb_dir = tmp_path / "thumbs"
    svg_dir.mkdir()
    thumb_dir.mkdir()

    monkeypatch.setattr(utils, "svg_data_path", svg_dir)
    monkeypatch.setattr(utils, "svg_data_thumb_path", thumb_dir)

    return svg_dir


def test_get_main_data_reads_json(tmp_path: Path) -> None:
    title_dir = tmp_path / "svg" / "topic"
    title_dir.mkdir(parents=True)
    stats = {"main_title": "Main", "values": 1}
    (title_dir / "files_stats.json").write_text(json.dumps(stats), encoding="utf-8")

    data = utils.get_main_data("topic")

    assert data == stats


def test_get_files_full_path_returns_all_files(tmp_path: Path) -> None:
    title_dir = tmp_path / "svg" / "folder" / "files"
    title_dir.mkdir(parents=True)
    (title_dir / "one.svg").write_text("<svg/>", encoding="utf-8")
    (title_dir / "two.txt").write_text("x", encoding="utf-8")

    files, path = utils.get_files_full_path("folder", "files")

    assert sorted(files) == ["one.svg", "two.txt"]
    assert path == title_dir


def test_get_files_filters_svg(tmp_path: Path) -> None:
    title_dir = tmp_path / "svg" / "folder" / "translated"
    title_dir.mkdir(parents=True)
    (title_dir / "one.svg").write_text("<svg/>", encoding="utf-8")
    (title_dir / "two.png").write_text("binary", encoding="utf-8")

    files, _ = utils.get_files("folder", "translated")

    assert files == ["one.svg"]


def test_get_languages_extracts_codes() -> None:
    translations = {
        "new": {
            "default_tspans_by_id": {},
            "section": {"fr": {}, "es": {}},
            "other": {"de": {}},
        }
    }

    langs = utils.get_languages("title", translations)

    assert langs == ["de", "es", "fr"]


def test_get_temp_title_prefers_file(tmp_path: Path) -> None:
    title_dir = tmp_path / "svg" / "topic"
    title_dir.mkdir(parents=True)
    (title_dir / "title.txt").write_text(" Display Title ", encoding="utf-8")

    assert utils.get_temp_title("topic") == "Display Title"
    assert utils.get_temp_title("missing") == "missing"


def test_get_informations_compiles_summary(tmp_path: Path) -> None:
    base = tmp_path / "svg" / "subject"
    (base / "files").mkdir(parents=True)
    (base / "translated").mkdir()

    (base / "files" / "one.svg").write_text("<svg/>", encoding="utf-8")
    (base / "files" / "two.svg").write_text("<svg/>", encoding="utf-8")
    (base / "translated" / "one.svg").write_text("<svg/>", encoding="utf-8")

    stats = {
        "main_title": "Example.svg",
        "titles": ["File:One.svg", "Other.svg"],
        "translations": {
            "new": {
                "default_tspans_by_id": {},
                "section": {"es": {}, "it": {}},
            }
        },
    }
    (base / "files_stats.json").write_text(json.dumps(stats), encoding="utf-8")
    (base / "title.txt").write_text("Subject", encoding="utf-8")

    info = utils.get_informations("subject")

    assert info["title"] == "Subject"
    assert info["len_files"]["downloaded"] == 2
    assert info["len_files"]["translated"] == 1
    assert info["len_files"]["not_translated"] == 1
    assert "File:Other.svg" in info["not_downloaded"]
