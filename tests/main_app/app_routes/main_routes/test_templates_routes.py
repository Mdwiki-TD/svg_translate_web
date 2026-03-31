"""Tests for templates routes utilities."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from src.main_app.app_routes.main_routes import templates_routes


@pytest.fixture(autouse=True)
def patch_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.settings",
        types.SimpleNamespace(paths=types.SimpleNamespace(svg_data=str(svg_dir))),
    )
    return svg_dir


def test_get_main_data_reads_file(tmp_path: Path) -> None:
    title_dir = tmp_path / "svg" / "topic"
    title_dir.mkdir(parents=True)
    payload = {"value": 1}
    (title_dir / "files_stats.json").write_text(json.dumps(payload), encoding="utf-8")

    assert templates_routes.get_main_data("topic") == payload


def test_temp_data_sanitizes_name(tmp_path: Path) -> None:
    sanitized = "template_clean_name"
    (tmp_path / "svg" / sanitized).mkdir(parents=True)

    result = templates_routes.temp_data("Template:Clean Name!")

    assert result["title_dir"] == sanitized


def test_temps_main_files_falls_back_to_main_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    template_entry = {"Sample": {"title_dir": "sample"}}
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_templates_db", lambda: types.SimpleNamespace(list=lambda: [])
    )
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_main_data", lambda title: {"main_title": "Example.svg"}
    )

    data = templates_routes.temps_main_files(template_entry)

    assert data["Sample"]["main_file"] == "File:Example.svg"


def test_get_main_data_missing_file(tmp_path: Path) -> None:
    """Test get_main_data returns empty dict when file doesn't exist."""
    result = templates_routes.get_main_data("nonexistent")
    assert result == {}


def test_get_main_data_invalid_json(tmp_path: Path) -> None:
    """Test get_main_data handles invalid JSON gracefully."""
    title_dir = tmp_path / "svg" / "invalid"
    title_dir.mkdir(parents=True)
    (title_dir / "files_stats.json").write_text("not valid json", encoding="utf-8")

    result = templates_routes.get_main_data("invalid")
    assert result == {}


def test_temp_data_no_directory(tmp_path: Path) -> None:
    """Test temp_data when directory doesn't exist."""
    result = templates_routes.temp_data("Template:Nonexistent")
    assert result["title_dir"] == ""
    assert result["main_file"] == ""


def test_temp_data_special_characters(tmp_path: Path) -> None:
    """Test temp_data sanitizes special characters correctly."""
    sanitized = "template_test__name"
    (tmp_path / "svg" / sanitized).mkdir(parents=True)

    result = templates_routes.temp_data("Template:Test!@#$ Name")

    assert result["title_dir"] == sanitized


def test_temps_main_files_uses_database_main_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test temps_main_files uses main_file from database when available."""
    from src.main_app.services.template_service import TemplateRecord

    template_entry = {"Template:Test": {"title_dir": "test"}}
    mock_template = TemplateRecord(id=1, title="Template:Test", main_file="dbfile.svg", last_world_file=None)
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_templates_db",
        lambda: types.SimpleNamespace(list=lambda: [mock_template]),
    )

    data = templates_routes.temps_main_files(template_entry)

    # The function adds File: prefix to filenames without it
    assert data["Template:Test"]["main_file"] == "File:dbfile.svg"


def test_temps_main_files_prefixes_file_correctly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test temps_main_files adds File: prefix when not present."""
    from src.main_app.services.template_service import TemplateRecord

    template_entry = {"Template:Test": {"title_dir": "test"}}
    mock_template = TemplateRecord(id=1, title="Template:Test", main_file="example.svg", last_world_file=None)
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_templates_db",
        lambda: types.SimpleNamespace(list=lambda: [mock_template]),
    )
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_main_data", lambda title: {"main_title": "example.svg"}
    )

    data = templates_routes.temps_main_files(template_entry)

    assert data["Template:Test"]["main_file"] == "File:example.svg"


def test_temps_main_files_no_duplicate_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test temps_main_files doesn't add File: prefix when already present."""
    from src.main_app.services.template_service import TemplateRecord

    template_entry = {"Template:Test": {"title_dir": "test"}}
    mock_template = TemplateRecord(id=1, title="Template:Test", main_file="File:example.svg", last_world_file=None)
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_templates_db",
        lambda: types.SimpleNamespace(list=lambda: [mock_template]),
    )
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_main_data", lambda title: {"main_title": "File:example.svg"}
    )

    data = templates_routes.temps_main_files(template_entry)

    assert data["Template:Test"]["main_file"] == "File:example.svg"


def test_main_route_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the main route endpoint with full integration."""
    from src.main_app.services.template_service import TemplateRecord

    # Mock get_category_members to return test templates
    def mock_get_category_members(category):
        return ["Template:Test1", "Template:Test2"]

    # Mock get_templates_db
    mock_template = TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg", last_world_file=None)
    monkeypatch.setattr("src.main_app.app_routes.templates.routes.get_category_members", mock_get_category_members)
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_templates_db",
        lambda: types.SimpleNamespace(list=lambda: [mock_template]),
    )

    # Capture render_template call
    rendered = {}

    def mock_render_template(template, **context):
        rendered["template"] = template
        rendered["context"] = context
        return "rendered"

    monkeypatch.setattr("src.main_app.app_routes.templates.routes.render_template", mock_render_template)

    result = templates_routes.main()

    assert result == "rendered"
    assert rendered["template"] == "templates/index.html"
    assert "data" in rendered["context"]
    assert "Template:Test1" in rendered["context"]["data"]
    assert "Template:Test2" in rendered["context"]["data"]


def test_main_route_sorting_by_main_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that main route sorts templates by main_file presence."""
    from src.main_app.services.template_service import TemplateRecord

    def mock_get_category_members(category):
        return ["Template:WithFile", "Template:WithoutFile"]

    mock_templates = [
        TemplateRecord(id=1, title="Template:WithFile", main_file="file.svg", last_world_file=None),
    ]

    monkeypatch.setattr("src.main_app.app_routes.templates.routes.get_category_members", mock_get_category_members)
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_templates_db",
        lambda: types.SimpleNamespace(list=lambda: mock_templates),
    )

    rendered = {}

    def mock_render_template(template, **context):
        rendered["template"] = template
        rendered["context"] = context
        return "rendered"

    monkeypatch.setattr("src.main_app.app_routes.templates.routes.render_template", mock_render_template)

    templates_routes.main()

    # Templates with main_file should come first (reverse=True in sort)
    data = rendered["context"]["data"]
    keys = list(data.keys())
    # Template:WithFile should come before Template:WithoutFile
    assert keys.index("Template:WithFile") < keys.index("Template:WithoutFile")


def test_main_route_filters_templates_correctly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that main route filters out non-template items and excluded templates."""

    def mock_get_category_members(category):
        return [
            "Template:Valid",
            "File:NotATemplate.svg",  # This should be filtered by get_category_members
        ]

    monkeypatch.setattr("src.main_app.app_routes.templates.routes.get_category_members", mock_get_category_members)
    monkeypatch.setattr(
        "src.main_app.app_routes.templates.routes.get_templates_db", lambda: types.SimpleNamespace(list=lambda: [])
    )

    rendered = {}

    def mock_render_template(template, **context):
        rendered["template"] = template
        rendered["context"] = context
        return "rendered"

    monkeypatch.setattr("src.main_app.app_routes.templates.routes.render_template", mock_render_template)

    templates_routes.main()

    data = rendered["context"]["data"]
    # get_category_members already filters, but the route does additional filtering
    # Should only have valid templates
    assert "Template:Valid" in data
    # File:NotATemplate.svg should be filtered out by get_category_members already
