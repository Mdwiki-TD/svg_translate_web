"""Tests for explorer routes."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Blueprint

from src.main_app.public.main_routes.explorer_routes import ExplorerRoutes


@pytest.fixture
def explorer():
    return ExplorerRoutes(Blueprint("explorer", __name__, url_prefix="/explorer"))


@pytest.fixture
def patch_templates(monkeypatch: pytest.MonkeyPatch) -> dict:
    captured: dict[str, dict] = {}

    def fake_render(template: str, **context):
        captured["template"] = template
        captured["context"] = context
        return template

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.render_template", fake_render)
    return captured


def test_by_title_downloaded_renders_list(explorer, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_files",
        lambda title, subdir: (["a.svg"], Path(f"/data/{subdir}")),
    )
    result = explorer.by_title_downloaded("topic")

    assert result == "explorer/explore_files.html"
    context = patch_templates["context"]
    assert context["files"] == ["a.svg"]
    assert context["subdir"] == "files"


def test_by_title_translated_sets_compare_link(explorer, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_files",
        lambda title, subdir: (["b.svg"], Path("/data")),
    )

    explorer.by_title_translated("topic")

    context = patch_templates["context"]
    assert context["subdir"] == "translated"
    assert context["compare_link"] is True


def test_by_title_not_translated_filters(explorer, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    def fake_get_files(title: str, subdir: str):
        if subdir == "files":
            return (["one.svg", "two.svg"], Path("/files"))
        return (["one.svg"], Path("/translated"))

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.get_files", fake_get_files)

    explorer.by_title_not_translated("topic")

    context = patch_templates["context"]
    assert context["files"] == ["two.svg"]


def test_by_title_renders_information(explorer, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_informations", lambda title: {"title": "Topic"}
    )

    explorer.by_title("topic")

    assert patch_templates["template"] == "explorer/folder.html"
    assert patch_templates["context"] == {"result": {"title": "Topic"}}


def test_main_lists_titles(explorer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    root = tmp_path / "data"
    (root / "alpha").mkdir(parents=True)
    (root / "beta").mkdir()
    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_svg_data_path", lambda: root)

    def fake_get_files(title: str, subdir: str):
        if title == "alpha" and subdir == "files":
            return (["a.svg"], Path("alpha/files"))
        if subdir == "translated":
            return (["a.svg"] if title == "alpha" else [], Path("t"))
        return ([], Path("empty"))

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.get_files", fake_get_files)

    explorer.main()

    data = patch_templates["context"]["data"]
    assert data["alpha"]["downloaded"] == 1
    assert data["beta"]["translated"] == 0


def test_serve_media_returns_directory(explorer, monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[tuple[str, str]] = []

    def fake_send(directory: str, filename: str):
        called.append((directory, filename))
        return SimpleNamespace(headers={})

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_svg_data_path", lambda: Path("/base"))
    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.send_from_directory", fake_send)

    _result = explorer.serve_media("title", "files", "file.svg")

    assert called[0][0].replace("\\", "/").endswith("base/title/files")
    assert called[0][1] == "file.svg"


def test_serve_thumb_prefers_cached_file(explorer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "data"
    thumbs = tmp_path / "thumbs"
    (base / "topic" / "files").mkdir(parents=True)
    (thumbs / "topic" / "files").mkdir(parents=True)
    (base / "topic" / "files" / "file.svg").write_text("<svg/>", encoding="utf-8")

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_svg_data_path", lambda: base)
    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_thumb_path", lambda: thumbs)

    def fake_save(src: Path, dest: Path) -> None:
        dest.write_text("thumb", encoding="utf-8")
        return

    responses: list = []

    def fake_send(directory: str, filename: str):
        responses.append((directory, filename))
        return SimpleNamespace(headers={})

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.save_thumb", fake_save)
    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.send_from_directory", fake_send)

    explorer.serve_thumb("topic", "files", "file.svg")

    path = responses[0][0].replace("\\", "/")
    assert path.endswith("thumbs/topic/files")


def test_compare_renders_template(explorer, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_svg_data_path", lambda: Path("/data"))
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.analyze_file", lambda path: {"file": path.name}
    )

    explorer.compare("title", "file.svg")

    context = patch_templates["context"]
    assert context["downloaded_result"] == {"file": "file.svg"}
    assert context["translated_result"] == {"file": "file.svg"}
