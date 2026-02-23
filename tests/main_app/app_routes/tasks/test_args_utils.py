"""Unit tests for args parsing utilities."""

import types

import pytest
from werkzeug.datastructures import MultiDict

from src.main_app.app_routes.tasks import args_utils


def _make_settings(disable_uploads: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(disable_uploads=disable_uploads)


def test_parse_args_upload_disabled_by_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(args_utils, "settings", _make_settings("1"))
    form = MultiDict([("upload", "1")])

    parsed = args_utils.parse_args(form)

    assert parsed.upload is False
    assert parsed.ignore_existing_task is False


def test_parse_args_manual_main_title_and_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(args_utils, "settings", _make_settings("0"))
    form = MultiDict(
        [
            ("manual_main_title", "  File:Example name.svg "),
            ("titles_limit", "50"),
            ("overwrite", "z"),
            ("upload", "1"),
            ("ignore_existing_task", "1"),
        ]
    )

    parsed = args_utils.parse_args(form)

    assert parsed.manual_main_title == "Example name.svg"
    assert parsed.titles_limit == 50
    assert parsed.overwrite is True
    assert parsed.upload is True
    assert parsed.ignore_existing_task is True


def test_parse_args_empty_manual_main_title(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(args_utils, "settings", _make_settings("0"))
    form = MultiDict([])

    parsed = args_utils.parse_args(form)

    assert parsed.manual_main_title is None
    assert parsed.titles_limit == 1000
