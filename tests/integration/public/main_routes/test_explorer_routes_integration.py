"""Tests for explorer routes."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Blueprint, Flask

from src.main_app.public.main_routes.explorer_routes import ExplorerRoutes


@pytest.fixture
def explorer_app():
    app = Flask(__name__)
    bp = Blueprint("explorer", __name__, url_prefix="/explorer")
    ExplorerRoutes(bp)
    app.register_blueprint(bp)
    return app


@pytest.fixture
def patch_templates(monkeypatch: pytest.MonkeyPatch) -> dict:
    captured: dict[str, dict] = {}

    def fake_render(template: str, **context):
        captured["template"] = template
        captured["context"] = context
        return template

    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.render_template",
        fake_render,
    )
    return captured


def test_by_title_downloaded_renders_list(explorer_app, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_files",
        lambda title, subdir: (["a.svg"], Path(f"/data/{subdir}")),
    )

    client = explorer_app.test_client()
    response = client.get("/explorer/topic/downloads")

    assert response.status_code == 200
    context = patch_templates["context"]
    assert context["files"] == ["a.svg"]
    assert context["subdir"] == "files"


def test_by_title_translated_sets_compare_link(
    explorer_app, monkeypatch: pytest.MonkeyPatch, patch_templates: dict
) -> None:
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_files",
        lambda title, subdir: (["b.svg"], Path("/data")),
    )

    client = explorer_app.test_client()
    client.get("/explorer/topic/translated")

    context = patch_templates["context"]
    assert context["subdir"] == "translated"
    assert context["compare_link"] is True


def test_by_title_not_translated_filters(explorer_app, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    def fake_get_files(title: str, subdir: str):
        if subdir == "files":
            return (["one.svg", "two.svg"], Path("/files"))
        return (["one.svg"], Path("/translated"))

    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_files",
        fake_get_files,
    )

    client = explorer_app.test_client()
    client.get("/explorer/topic/not_translated")

    context = patch_templates["context"]
    assert context["files"] == ["two.svg"]


def test_by_title_renders_information(explorer_app, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_informations",
        lambda title: {"title": "Topic"},
    )

    client = explorer_app.test_client()
    client.get("/explorer/topic")

    assert patch_templates["template"] == "explorer/folder.html"
    assert patch_templates["context"] == {"result": {"title": "Topic"}}


def test_main_lists_titles(
    explorer_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, patch_templates: dict
) -> None:
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

    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.get_files",
        fake_get_files,
    )

    client = explorer_app.test_client()
    client.get("/explorer/")

    data = patch_templates["context"]["data"]
    assert data["alpha"]["downloaded"] == 1
    assert data["beta"]["translated"] == 0


def test_serve_media_returns_directory(explorer_app, monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[tuple[str, str]] = []

    def fake_send(directory: str, filename: str):
        called.append((directory, filename))
        return SimpleNamespace(headers={})

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_svg_data_path", lambda: Path("/base"))
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.send_from_directory",
        fake_send,
    )

    client = explorer_app.test_client()
    client.get("/explorer/media/title/files/file.svg")

    assert called[0][0].replace("\\", "/").endswith("base/title/files")
    assert called[0][1] == "file.svg"


def test_serve_thumb_prefers_cached_file(explorer_app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "data"
    thumbs = tmp_path / "thumbs"
    (base / "topic" / "files").mkdir(parents=True)
    (thumbs / "topic" / "files").mkdir(parents=True)
    (base / "topic" / "files" / "file.svg").write_text("<svg/>", encoding="utf-8")

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_svg_data_path", lambda: base)
    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_thumb_path", lambda: thumbs)

    def fake_save(src: Path, dest: Path) -> None:
        dest.write_text("thumb", encoding="utf-8")

    responses: list = []

    def fake_send(directory: str, filename: str):
        responses.append((directory, filename))
        return SimpleNamespace(headers={})

    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.save_thumb", fake_save)
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.send_from_directory",
        fake_send,
    )

    client = explorer_app.test_client()
    client.get("/explorer/media_thumb/topic/files/file.svg")

    path = responses[0][0].replace("\\", "/")
    assert path.endswith("thumbs/topic/files")


def test_compare_renders_template(explorer_app, monkeypatch: pytest.MonkeyPatch, patch_templates: dict) -> None:
    monkeypatch.setattr("src.main_app.public.main_routes.explorer_routes.load_svg_data_path", lambda: Path("/data"))
    monkeypatch.setattr(
        "src.main_app.public.main_routes.explorer_routes.analyze_file",
        lambda path: {"file": path.name},
    )

    client = explorer_app.test_client()
    client.get("/explorer/compare/title/file.svg")

    context = patch_templates["context"]
    assert context["downloaded_result"] == {"file": "file.svg"}
    assert context["translated_result"] == {"file": "file.svg"}
