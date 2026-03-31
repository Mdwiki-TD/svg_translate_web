"""Unit tests for args parsing utilities."""

from werkzeug.datastructures import MultiDict

from src.main_app.app_routes.utils import args_utils


def test_parse_args_upload_disabled_by_config() -> None:
    form = MultiDict([("upload", "1")])

    parsed = args_utils.parse_args(form, "1")

    assert parsed.upload is False
    assert parsed.ignore_existing_task is False


def test_parse_args_manual_main_title_and_limits() -> None:
    form = MultiDict(
        [
            ("manual_main_title", "  File:Example name.svg "),
            ("titles_limit", "50"),
            ("overwrite", "z"),
            ("upload", "1"),
            ("ignore_existing_task", "1"),
        ]
    )

    parsed = args_utils.parse_args(form, "0")

    assert parsed.manual_main_title == "Example name.svg"
    assert parsed.titles_limit == 50
    assert parsed.overwrite is True
    assert parsed.upload is True
    assert parsed.ignore_existing_task is True


def test_parse_args_empty_manual_main_title() -> None:
    form = MultiDict([])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.manual_main_title is None
    assert parsed.titles_limit == 1000
