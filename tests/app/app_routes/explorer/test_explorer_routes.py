"""Tests for explorer routes."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from src.app.app_routes.explorer import routes


@pytest.fixture
def patch_templates(monkeypatch: pytest.MonkeyPatch) -> dict:
    captured: dict[str, dict] = {}

    def fake_render(template: str, **context):
        captured["template"] = template
        captured["context"] = context
        return template

    monkeypatch.setattr(routes, "render_template", fake_render)
    return captured


def test_by_title_downloaded_renders_list(monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(routes, "get_files", lambda title, subdir: (["a.svg"], Path(f"/data/{subdir}")))
    monkeypatch.setattr(routes, "get_temp_title", lambda title: "Title")

    result = routes.by_title_downloaded("topic")

    assert result == "explorer/explore_files.html"
    context = patch_templates["context"]
    assert context["files"] == ["a.svg"]
    assert context["subdir"] == "files"
    assert context["title"] == "Title"


def test_by_title_translated_sets_compare_link(monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(routes, "get_files", lambda title, subdir: (["b.svg"], Path("/data")))
    monkeypatch.setattr(routes, "get_temp_title", lambda title: "Sample")

    routes.by_title_translated("topic")

    context = patch_templates["context"]
    assert context["subdir"] == "translated"
    assert context["compare_link"] is True


def test_by_title_not_translated_filters(monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    def fake_get_files(title: str, subdir: str):
        if subdir == "files":
            return (["one.svg", "two.svg"], Path("/files"))
        return (["one.svg"], Path("/translated"))

    monkeypatch.setattr(routes, "get_files", fake_get_files)
    monkeypatch.setattr(routes, "get_temp_title", lambda title: "Topic")

    routes.by_title_not_translated("topic")

    context = patch_templates["context"]
    assert context["files"] == ["two.svg"]
    assert context["title"] == "Topic"


def test_by_title_renders_information(monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(routes, "get_informations", lambda title: {"title": "Topic"})

    routes.by_title("topic")

    assert patch_templates["template"] == "explorer/folder.html"
    assert patch_templates["context"] == {"result": {"title": "Topic"}}


def test_main_lists_titles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    root = tmp_path / "data"
    (root / "alpha").mkdir(parents=True)
    (root / "beta").mkdir()
    monkeypatch.setattr(routes, "svg_data_path", root)

    def fake_get_files(title: str, subdir: str):
        if title == "alpha" and subdir == "files":
            return (["a.svg"], Path("alpha/files"))
        if subdir == "translated":
            return (["a.svg"] if title == "alpha" else [], Path("t"))
        return ([], Path("empty"))

    monkeypatch.setattr(routes, "get_files", fake_get_files)

    routes.main()

    data = patch_templates["context"]["data"]
    assert data["alpha"]["downloaded"] == 1
    assert data["beta"]["translated"] == 0


def test_serve_media_returns_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[tuple[str, str]] = []

    def fake_send(directory: str, filename: str):
        called.append((directory, filename))
        return directory

    monkeypatch.setattr(routes, "svg_data_path", Path("/base"))
    monkeypatch.setattr(routes, "send_from_directory", fake_send)

    result = routes.serve_media("title", "files", "file.svg")

    assert result in ["/base/title/files", r"I:\base\title\files"]
    # assert called == [("/base/title/files", "file.svg")]
    assert called[0][1] == "file.svg"


def test_serve_thumb_prefers_cached_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "data"
    thumbs = tmp_path / "thumbs"
    (base / "topic" / "files").mkdir(parents=True)
    (thumbs / "topic" / "files").mkdir(parents=True)
    (base / "topic" / "files" / "file.svg").write_text("<svg/>", encoding="utf-8")

    monkeypatch.setattr(routes, "svg_data_path", base)
    monkeypatch.setattr(routes, "svg_data_thumb_path", thumbs)

    def fake_save(src: Path, dest: Path) -> None:
        dest.write_text("thumb", encoding="utf-8")
        return None

    responses = []

    def fake_send(directory: str, filename: str):
        responses.append((directory, filename))
        return directory

    monkeypatch.setattr(routes, "save_thumb", fake_save)
    monkeypatch.setattr(routes, "send_from_directory", fake_send)

    result = routes.serve_thumb("topic", "files", "file.svg")

    assert result.endswith("files")
    path = responses[0][0].replace("\\", "/")
    assert path.endswith("thumbs/topic/files")


def test_compare_renders_template(monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(routes, "svg_data_path", Path("/data"))
    monkeypatch.setattr(routes, "analyze_file", lambda path: {"file": path.name})

    routes.compare("title", "file.svg")

    context = patch_templates["context"]
    assert context["downloaded_result"] == {"file": "file.svg"}
    assert context["translated_result"] == {"file": "file.svg"}
