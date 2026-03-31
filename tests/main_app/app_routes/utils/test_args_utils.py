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


def test_parse_args_upload_enabled_when_not_disabled() -> None:
    """Upload is allowed when disable_uploads is not '1'."""
    form = MultiDict([("upload", "1")])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.upload is True


def test_parse_args_upload_disabled_explicit_zero() -> None:
    """disable_uploads='1' disables upload even if form has upload checked."""
    form = MultiDict([("upload", "1")])

    parsed = args_utils.parse_args(form, "1")

    assert parsed.upload is False


def test_parse_args_upload_not_in_form() -> None:
    """Upload is False when not present in form and uploads are enabled."""
    form = MultiDict([])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.upload is False


def test_parse_args_manual_main_title_file_prefix_lowercase() -> None:
    """manual_main_title strips 'file:' prefix (case-insensitive check via lower())."""
    form = MultiDict([("manual_main_title", "file:My Image.svg")])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.manual_main_title == "My Image.svg"


def test_parse_args_manual_main_title_only_file_colon() -> None:
    """manual_main_title becomes None when only 'File:' is provided."""
    form = MultiDict([("manual_main_title", "File:")])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.manual_main_title is None


def test_parse_args_manual_main_title_whitespace_only() -> None:
    """manual_main_title becomes None when only whitespace is provided."""
    form = MultiDict([("manual_main_title", "   ")])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.manual_main_title is None


def test_parse_args_overwrite_not_present() -> None:
    """overwrite is False when not present in form."""
    form = MultiDict([])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.overwrite is False


def test_parse_args_default_titles_limit() -> None:
    """Default titles_limit is 1000."""
    form = MultiDict([])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.titles_limit == 1000


def test_parse_args_custom_titles_limit() -> None:
    """titles_limit reflects form value when provided."""
    form = MultiDict([("titles_limit", "250")])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.titles_limit == 250


def test_parse_args_disable_uploads_other_string() -> None:
    """Upload is allowed when disable_uploads is some string other than '1'."""
    form = MultiDict([("upload", "1")])

    parsed = args_utils.parse_args(form, "false")

    assert parsed.upload is True


def test_parse_args_ignore_existing_task_not_set() -> None:
    """ignore_existing_task defaults to False when not in form."""
    form = MultiDict([])

    parsed = args_utils.parse_args(form, "0")

    assert parsed.ignore_existing_task is False